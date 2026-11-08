#!/usr/bin/env python3
"""
Fast replacement for fetch_tiles.py.

Same output naming ({layer}_z{z}_{x}_{y}.png), same idempotent skip, but:
  * ONE persistent aiohttp connection pool (keep-alive) instead of a fresh TLS
    handshake per tile -> the real bottleneck removed.
  * multiple in-flight requests (default 32), spread across mt0..mt3.
  * retries with exponential backoff + jitter; honours 429/403.
  * atomic writes (.tmp -> os.replace).
  * resumable: skips tiles already on disk (>100 bytes).

Usage:
  python fetch_tiles_fast.py                       # m then y, z6..z13, Pakistan
  python fetch_tiles_fast.py --layers m --zmin 6 --zmax 13
  python fetch_tiles_fast.py --concurrency 48
"""
import argparse, asyncio, math, os, random, sys, time

import aiohttp

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
HOSTS = ("mt0.google.com", "mt1.google.com", "mt2.google.com", "mt3.google.com")
PAKISTAN = (23.69, 37.13, 60.87, 77.83)


def tile_range(lat_min, lat_max, lng_min, lng_max, z):
    n = 2 ** z
    x0 = int((lng_min + 180) / 360 * n)
    x1 = int((lng_max + 180) / 360 * n)

    def ty(lat):
        r = math.radians(lat)
        return int((1 - math.log(math.tan(r) + 1 / math.cos(r)) / math.pi) / 2 * n)

    y0, y1 = ty(lat_max), ty(lat_min)
    return max(0, x0), min(x1 + 1, n), max(0, y0), min(y1 + 1, n)


def build_jobs(layers, zmin, zmax, bboxes):
    jobs = []
    seen = set()
    for layer in layers:
        for z in range(zmin, zmax + 1):
            for bbox in bboxes:
                x0, x1, y0, y1 = tile_range(*bbox, z)
                for yy in range(y0, y1):
                    for xx in range(x0, x1):
                        key = (layer, z, xx, yy)
                        if key not in seen:
                            seen.add(key)
                            jobs.append(key)
    return jobs


async def fetch_one(session, sem, job, outdir, stats, retries):
    layer, z, x, y = job
    fn = os.path.join(outdir, f"{layer}_z{z}_{x}_{y}.png")
    if os.path.exists(fn) and os.path.getsize(fn) > 100:
        stats["skip"] += 1
        return
    url = f"https://{random.choice(HOSTS)}/vt/lyrs={layer}&x={x}&y={y}&z={z}"
    for attempt in range(retries):
        try:
            async with sem:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as r:
                    status = r.status
                    data = await r.read()
            if status == 200 and len(data) > 100:
                tmp = fn + ".tmp"
                with open(tmp, "wb") as f:
                    f.write(data)
                os.replace(tmp, fn)
                stats["ok"] += 1
                return
            if status in (429, 403, 500, 502, 503, 504):
                stats[f"http{status}"] += 1
                await asyncio.sleep(min(30, 1.5 * (attempt + 1)) + random.random())
            else:
                stats["bad"] += 1
                await asyncio.sleep(0.5 * (attempt + 1))
        except Exception:
            stats["err"] += 1
            await asyncio.sleep(0.5 * (attempt + 1) + random.random() * 0.5)
    stats["fail"] += 1


async def run(args):
    jobs = build_jobs(args.layers, args.zmin, args.zmax, args.bboxes)
    os.makedirs(args.out, exist_ok=True)
    print(f"queued {len(jobs)} tiles  concurrency={args.concurrency}", flush=True)

    stats = {"ok": 0, "skip": 0, "fail": 0, "bad": 0, "err": 0,
             "http429": 0, "http403": 0, "http500": 0, "http502": 0,
             "http503": 0, "http504": 0}
    queue = asyncio.Queue()
    for j in jobs:
        queue.put_nowait(j)

    connector = aiohttp.TCPConnector(limit=args.concurrency,
                                     limit_per_host=args.concurrency,
                                     ttl_dns_cache=300)
    done = 0
    start = time.time()
    last = start
    failed = []

    async with aiohttp.ClientSession(connector=connector,
                                     headers={"User-Agent": UA}) as session:
        sem = asyncio.Semaphore(args.concurrency)

        async def worker():
            nonlocal done, last
            while True:
                try:
                    job = queue.get_nowait()
                except asyncio.QueueEmpty:
                    return
                before = stats["fail"]
                await fetch_one(session, sem, job, args.out, stats, args.retries)
                if stats["fail"] > before:
                    failed.append(job)
                done += 1
                if done % 500 == 0:
                    now = time.time()
                    rate = (done - (stats["skip"])) / max(0.001, now - start)
                    print(f"{done}/{len(jobs)}  ok={stats['ok']} skip={stats['skip']} "
                          f"fail={stats['fail']}  429={stats['http429']} 403={stats['http403']} "
                          f"~{rate:.0f} new tiles/s ({(now-start)/60:.1f} min)", flush=True)
                    last = now

        tasks = [asyncio.create_task(worker()) for _ in range(args.concurrency)]
        await asyncio.gather(*tasks)

    if failed:
        with open(os.path.join(args.out, "failed.txt"), "a") as f:
            for layer, z, x, y in failed:
                f.write(f"{layer} {z} {x} {y}\n")

    dt = time.time() - start
    print(f"DONE {dt/60:.1f} min  ok={stats['ok']} skip={stats['skip']} "
          f"fail={stats['fail']}  429={stats['http429']} 403={stats['http403']}", flush=True)


def parse_bbox(s):
    lat_min, lat_max, lng_min, lng_max = (float(v) for v in s.split(","))
    return (lat_min, lat_max, lng_min, lng_max)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--layers", default="m,y")
    p.add_argument("--zmin", type=int, default=6)
    p.add_argument("--zmax", type=int, default=13)
    p.add_argument("--bbox", type=parse_bbox, default=PAKISTAN)
    p.add_argument("--areas-file", default=None,
                   help="file with one bbox per line: lat_min lat_max lng_min lng_max")
    p.add_argument("--out", default=r"G:\sketcyshitx2\data\tiles")
    p.add_argument("--concurrency", type=int, default=32)
    p.add_argument("--retries", type=int, default=4)
    p.add_argument("--limit", type=int, default=0, help="stop after N jobs (benchmarking)")
    args = p.parse_args()
    args.layers = tuple(a.strip() for a in args.layers.split(",") if a.strip())
    if args.areas_file:
        bboxes = []
        with open(args.areas_file, encoding="utf-8") as f:
            for line in f:
                line = line.split("#", 1)[0].strip()
                if not line:
                    continue
                lat_min, lat_max, lng_min, lng_max = (float(v) for v in line.replace(",", " ").split())
                bboxes.append((lat_min, lat_max, lng_min, lng_max))
        args.bboxes = bboxes or [args.bbox]
    else:
        args.bboxes = [args.bbox]
    if args.limit:
        # trim queue by monkeypatching after build
        orig = build_jobs
        globals()["build_jobs"] = lambda *a, **k: orig(*a, **k)[:args.limit]
    asyncio.run(run(args))


if __name__ == "__main__":
    main()
