#!/usr/bin/env python3
r"""
Fast dir -> MBTiles builder.

Optimised for the flat 870k-file tile dump:
  * parallel reads (ThreadPoolExecutor)
  * plain INSERT into an index-less table, unique index created ONCE at the end
  * commit per chunk, PRAGMAs tuned for bulk load
  * XYZ -> TMS y-flip
"""
import argparse, math, os, re, sqlite3, sys, time
from concurrent.futures import ThreadPoolExecutor

PAT = re.compile(r"^(?P<layer>[a-z]+)_z(?P<z>\d+)_(?P<x>\d+)_(?P<y>\d+)\.png$")


def sniff(data):
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if data.startswith(b"\xff\xd8\xff"):
        return "jpg"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    return None


def lon_of(x, z):
    return x / (2 ** z) * 360.0 - 180.0


def lat_of(y, z):
    n = 2 ** z
    return math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * y / n))))


def scan(tiledir, layer, zmin, zmax):
    tiles = []
    fmt = None
    sampled = 0
    with os.scandir(tiledir) as it:
        for e in it:
            m = PAT.match(e.name)
            if not m or m.group("layer") != layer:
                continue
            z = int(m.group("z"))
            if z < zmin or z > zmax:
                continue
            if fmt is None and sampled < 25:
                with open(e.path, "rb") as f:
                    fmt = sniff(f.read(12))
                sampled += 1
            tiles.append((z, int(m.group("x")), int(m.group("y")), e.path))
    return tiles, fmt


def read_one(t):
    z, x, y, path = t
    with open(path, "rb") as f:
        data = f.read()
    return (z, x, (1 << z) - 1 - y, data)


def build(tiles, out, fmt, zmin, zmax, name, attribution, threads=16, chunk=40000):
    if os.path.exists(out):
        os.remove(out)
    con = sqlite3.connect(out)
    cur = con.cursor()
    cur.execute("PRAGMA journal_mode=OFF")
    cur.execute("PRAGMA synchronous=OFF")
    cur.execute("PRAGMA cache_size=-262144")   # 256 MB
    cur.execute("PRAGMA temp_store=MEMORY")
    cur.execute("PRAGMA locking_mode=EXCLUSIVE")
    cur.execute("CREATE TABLE metadata (name TEXT, value TEXT)")
    cur.execute("CREATE TABLE tiles (zoom_level INTEGER, tile_column INTEGER, tile_row INTEGER, tile_data BLOB)")

    zt = [t for t in tiles if t[0] == zmin]
    w = min(lon_of(x, zmin) for _, x, _, _ in zt)
    e_ = max(lon_of(x + 1, zmin) for _, x, _, _ in zt)
    n_ = max(lat_of(y, zmin) for _, _, y, _ in zt)
    s = min(lat_of(y + 1, zmin) for _, _, y, _ in zt)
    bounds = f"{w:.6f},{s:.6f},{e_:.6f},{n_:.6f}"

    meta = {
        "name": name, "format": fmt, "bounds": bounds,
        "minzoom": str(zmin), "maxzoom": str(zmax), "type": "baselayer",
        "version": "1", "attribution": attribution,
        "generator": "tiles_to_mbtiles_fast.py",
    }
    cur.executemany("INSERT INTO metadata (name, value) VALUES (?, ?)", list(meta.items()))

    t0 = time.time()
    total = len(tiles)
    done = 0
    with ThreadPoolExecutor(threads) as ex:
        for i in range(0, total, chunk):
            part = tiles[i:i + chunk]
            rows = list(ex.map(read_one, part))
            cur.executemany("INSERT INTO tiles VALUES (?,?,?,?)", rows)
            con.commit()
            done += len(rows)
            print(f"  {done}/{total}  {time.time()-t0:.0f}s", flush=True)

    cur.execute("CREATE UNIQUE INDEX tile_index ON tiles (zoom_level, tile_column, tile_row)")
    con.commit()
    cur.execute("ANALYZE")
    con.commit()
    con.close()
    print(f"DONE {out}  {os.path.getsize(out)/1024/1024:.1f} MB  bounds={bounds}  {time.time()-t0:.0f}s", flush=True)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--dir", default=r"G:\sketcyshitx2\data\tiles")
    p.add_argument("--layer", required=True)
    p.add_argument("--zmin", type=int, default=0)
    p.add_argument("--zmax", type=int, default=30)
    p.add_argument("--out", required=True)
    p.add_argument("--name", default=None)
    p.add_argument("--attribution", default="")
    p.add_argument("--threads", type=int, default=16)
    args = p.parse_args()

    t0 = time.time()
    tiles, fmt = scan(args.dir, args.layer, args.zmin, args.zmax)
    print(f"scanned {len(tiles)} tiles in {time.time()-t0:.0f}s  format={fmt}", flush=True)
    if not tiles:
        sys.exit("no tiles")
    zmin = min(t[0] for t in tiles)
    zmax = max(t[0] for t in tiles)
    build(tiles, args.out, fmt or "png", zmin, zmax,
          args.name or f"Pakistan {args.layer} z{zmin}-{zmax}",
          args.attribution, threads=args.threads)


if __name__ == "__main__":
    main()
