import json, os, shutil

SRC = r"G:\sketcyshitx2\data"
DST = r"G:\sketcyshitx2\android-assets"

os.makedirs(os.path.join(DST, "styles"), exist_ok=True)
os.makedirs(os.path.join(DST, "assets"), exist_ok=True)

# 1) vector tiles (+ POI tiles if present)
shutil.copy2(os.path.join(SRC, "pakistan_vector.pmtiles"), os.path.join(DST, "pakistan_vector.pmtiles"))
places = os.path.join(SRC, "pakistan_places.pmtiles")
if os.path.exists(places):
    shutil.copy2(places, os.path.join(DST, "pakistan_places.pmtiles"))
search = os.path.join(SRC, "places_search.db")
if os.path.exists(search):
    shutil.copy2(search, os.path.join(DST, "places_search.db"))

# 2) sprite + fonts
for sub in ("sprite", "fonts"):
    s = os.path.join(SRC, "assets", sub)
    d = os.path.join(DST, "assets", sub)
    if os.path.isdir(d):
        shutil.rmtree(d)
    shutil.copytree(s, d)

# 3) app styles: point the source at the bundled pmtiles
for theme in ("light", "dark", "field"):
    st = json.load(open(os.path.join(SRC, f"style_{theme}.json"), encoding="utf-8"))
    st["sources"]["v"] = {"type": "vector", "url": "pmtiles://pakistan_vector.pmtiles",
                          "minzoom": 0, "maxzoom": 14}
    st["sprite"] = "assets/sprite/sprite"
    st["glyphs"] = "assets/fonts/{fontstack}/{range}.pbf"
    json.dump(st, open(os.path.join(DST, "styles", f"style_{theme}.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

print("packaged ->", DST)
for root, dirs, files in os.walk(DST):
    depth = root[len(DST):].count(os.sep)
    if depth <= 1:
        print("  " + root[len(DST) + 1:] + "\\  (" + str(len(files)) + " files)")
print("total MB:", round(sum(os.path.getsize(os.path.join(r, f)) for r, _, fs in os.walk(DST) for f in fs) / 1024 / 1024, 1))
