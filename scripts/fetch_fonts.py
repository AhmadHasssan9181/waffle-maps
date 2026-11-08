import os, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor

ROOT = r"G:\sketcyshitx2\data\assets\fonts"
FONTS = ["Noto Sans Regular", "Noto Sans Medium", "Noto Sans Bold", "Noto Sans Italic"]
RANGES = [f"{i}-{i+255}" for i in range(0, 65536, 256)]
BASE = "https://protomaps.github.io/basemaps-assets/fonts"


def dl(job):
    font, r = job
    d = os.path.join(ROOT, font)
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, r + ".pbf")
    if os.path.exists(p) and os.path.getsize(p) > 0:
        return "skip"
    url = f"{BASE}/{urllib.parse.quote(font)}/{r}.pbf"
    try:
        data = urllib.request.urlopen(url, timeout=30).read()
        with open(p, "wb") as f:
            f.write(data)
        return "ok"
    except Exception:
        return "miss"


jobs = [(f, r) for f in FONTS for r in RANGES]
counts = {"ok": 0, "skip": 0, "miss": 0}
with ThreadPoolExecutor(24) as ex:
    for res in ex.map(dl, jobs):
        counts[res] += 1
print(counts)
for f in FONTS:
    d = os.path.join(ROOT, f)
    if os.path.isdir(d):
        print(f, len(os.listdir(d)), "ranges")
