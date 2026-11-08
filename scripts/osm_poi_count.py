import collections, sys, time
import osmium

pbf = sys.argv[1] if len(sys.argv) > 1 else r"G:\sketcyshitx2\data\pakistan-latest.osm.pbf"
KEYS = ("amenity", "shop", "tourism", "leisure", "healthcare", "emergency",
        "office", "craft", "public_transport", "historic")
counts = collections.Counter()
total = 0

t0 = time.time()
fp = (osmium.FileProcessor(pbf, osmium.osm.NODE | osmium.osm.WAY | osmium.osm.RELATION)
      .with_filter(osmium.filter.KeyFilter(*KEYS)))

seen = 0
for obj in fp:
    seen += 1
    d = {t.k: t.v for t in obj.tags}
    for k in KEYS:
        v = d.get(k)
        if v:
            counts[f"{k}={v}"] += 1
            total += 1

print(f"scanned in {time.time() - t0:.1f}s  matched objects={seen}")
print(f"total tagged features: {total}")
for k, v in counts.most_common(60):
    print(f"{v:>9}  {k}")

print("\n--- disaster-critical ---")
CRIT = ["amenity=hospital", "amenity=clinic", "amenity=pharmacy", "amenity=doctors",
        "amenity=fire_station", "amenity=police", "amenity=shelter",
        "amenity=drinking_water", "amenity=toilets", "amenity=fuel",
        "amenity=townhall", "amenity=community_centre", "amenity=social_facility",
        "healthcare=hospital", "healthcare=clinic", "healthcare=pharmacy",
        "healthcare=doctor", "emergency=ambulance_station",
        "emergency=fire_station", "emergency=water_tank"]
for k in CRIT:
    print(f"{counts.get(k, 0):>9}  {k}")
