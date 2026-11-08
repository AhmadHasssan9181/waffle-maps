"""Generate Urdu and dual-language variants of the styles (dev + Android)."""
import copy, json, os

DEV = r"G:\sketcyshitx2\data"
AND = r"G:\sketcyshitx2\android-assets\styles"
LABELS = ["place-city", "place-town", "place-village", "place-suburb",
          "road-label", "water-name", "aerodrome", "peak"]


def tf(lang):
    if lang == "ur":
        return ["coalesce", ["get", "name:ur"], ["get", "name"], ""]
    return ["format",
            ["coalesce", ["get", "name:en"], ["get", "name"], ""], {},
            "\n", {},
            ["coalesce", ["get", "name:ur"], ""]]


for theme in ("light", "dark", "field"):
    for base_dir in (DEV, AND):
        src = os.path.join(base_dir, f"style_{theme}.json")
        if not os.path.exists(src):
            continue
        base = json.load(open(src, encoding="utf-8"))
        for lang in ("ur", "both"):
            s = copy.deepcopy(base)
            for l in s["layers"]:
                if l.get("id") in LABELS and l.get("type") == "symbol":
                    l.setdefault("layout", {})["text-field"] = tf(lang)
            out = os.path.join(base_dir, f"style_{theme}_{lang}.json")
            json.dump(s, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            print("wrote", out)
print("done")
