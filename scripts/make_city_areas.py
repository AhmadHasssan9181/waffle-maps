"""Derive urban areas (city/town boxes) from the Pakistan OSM PBF for high-zoom scraping."""
import math, sys
import osmium

pbf = sys.argv[1] if len(sys.argv) > 1 else r"G:\sketcyshitx2\data\pakistan-latest.osm.pbf"
out = sys.argv[2] if len(sys.argv) > 2 else r"G:\sketcyshitx2\data\areas_urban.txt"
minpop = int(sys.argv[3]) if len(sys.argv) > 3 else 100000
maxc = int(sys.argv[4]) if len(sys.argv) > 4 else 80


def tile_range(lat_min, lat_max, lng_min, lng_max, z):
    n = 2 ** z
    x0 = int((lng_min + 180) / 360 * n)
    x1 = int((lng_max + 180) / 360 * n)

    def ty(lat):
        r = math.radians(lat)
        return int((1 - math.log(math.tan(r) + 1 / math.cos(r)) / math.pi) / 2 * n)

    y0, y1 = ty(lat_max), ty(lat_min)
    return max(0, x0), min(x1 + 1, n), max(0, y0), min(y1 + 1, n)


rows = []
fp = osmium.FileProcessor(pbf, osmium.osm.NODE).with_filter(osmium.filter.KeyFilter("place"))
for o in fp:
    d = {t.k: t.v for t in o.tags}
    place = d.get("place")
    if place not in ("city", "town"):
        continue
    try:
        pop = int(d.get("population", "0"))
    except ValueError:
        pop = 0
    loc = o.location
    if not loc.valid():
        continue
    rows.append((pop, place, loc.lat, loc.lon, d.get("name", "")))

rows.sort(key=lambda r: r[0], reverse=True)


def radius(pop):
    if pop >= 2_000_000:
        return 0.40
    if pop >= 1_000_000:
        return 0.30
    if pop >= 500_000:
        return 0.22
    if pop >= 200_000:
        return 0.16
    if pop >= 100_000:
        return 0.12
    return 0.09


selected = []
for pop, place, lat, lon, name in rows:
    if len(selected) >= maxc:
        break
    if any(abs(lat - s[1]) < 0.15 and abs(lon - s[2]) < 0.15 for s in selected):
        continue
    selected.append((name, lat, lon, radius(pop), pop))

with open(out, "w", encoding="utf-8") as f:
    f.write("# lat_min lat_max lng_min lng_max  # name\n")
    for name, lat, lon, r, pop in selected:
        f.write(f"{lat - r:.4f} {lat + r:.4f} {lon - r:.4f} {lon + r:.4f}  # {name} ({pop})\n")

print(f"areas={len(selected)} -> {out}")
print("\ntile estimate (deduped):")
for z in (14, 15, 16, 17):
    seen = set()
    for name, lat, lon, r, pop in selected:
        x0, x1, y0, y1 = tile_range(lat - r, lat + r, lon - r, lon + r, z)
        for yy in range(y0, y1):
            for xx in range(x0, x1):
                seen.add((xx, yy))
    print(f"  z{z}: {len(seen):>10,} tiles  (~{len(seen)*7.5/1024:.0f} MB)")
print("\nfirst 15:")
for name, lat, lon, r, pop in selected[:15]:
    safe = name.encode("ascii", "replace").decode()
    print(f"  {safe:28s} {lat:8.3f},{lon:9.3f}  r={r}  pop={pop}")
