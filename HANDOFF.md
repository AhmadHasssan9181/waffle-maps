# W.A.F.F.L.E. Map Stack — Handoff / Context

Everything below was built in `G:\sketcyshitx2`. The goal: a **fully offline, MapLibre-native
vector basemap of Pakistan with 809k POIs, bilingual labels, and offline search**, to replace
Waffle's current label-less local map and feed its GraphHopper offline routing.

---

## 1. TL;DR

| Artifact | Path | Size |
|---|---|---|
| Basemap vector tiles | `android-assets/pakistan_vector.pmtiles` | 266.1 MB |
| POI vector tiles (809,824 places) | `android-assets/pakistan_places.pmtiles` | 214.5 MB |
| Offline search index (SQLite FTS5) | `android-assets/places_search.db` | 104.4 MB |
| Styles (9 variants) | `android-assets/styles/` | small |
| Sprite + glyphs | `android-assets/assets/` | ~11 MB |
| README | `android-assets/README.md` | — |

Total bundle: **596 MB**. Both PMTiles verify with `pmtiles verify`.

- Basemap: **OpenMapTiles schema**, z0–14, MVT/gzip, clustered PMTiles (Planetiler).
- POIs: **Overture Maps** release `2026-10-21.0`, z11–14, layer `place`, 809,824 named places.
- Search: SQLite **FTS5**, 809,824 names, prefix + ranked.
- Themes: **light / dark / field** × languages **English / Urdu / both**.
- Attribution: `© OpenMapTiles © OpenStreetMap contributors © Overture Maps Foundation`.

---

## 2. Data sources

| Source | What | Where |
|---|---|---|
| OpenStreetMap (Geofabrik Pakistan) | roads, places, water, buildings, POIs | `data/pakistan-latest.osm.pbf` (~158 MB, refreshed 2026‑11‑07) |
| Natural Earth 10m ocean | ocean water polygons (canonical OSM water host was IP-blocked) | `data/sources/ne_10m_ocean.zip` |
| Overture Maps places `2026-10-21.0` | 809,824 named places for Pakistan bbox (60.8–77.3E, 23.3–37.2N) | S3 `overturemaps-us-west-2` |

Google raster tiles were also scraped earlier (`data/tiles/`, ~5.6 GB) but are **images only** —
they cannot yield structured amenities. They are legacy/fallback, not part of the final stack.

---

## 3. Basemap vector tiles

**File:** `data/pakistan_vector.pmtiles` → `android-assets/pakistan_vector.pmtiles`

- Built with **Planetiler 0.10.2** (`tools/planetiler.jar`) from the OSM PBF.
- `--maxzoom=14 --tile_compression=gzip`, OpenMapTiles profile, PMTiles output.
- Result: **253,618 tiles**, MVT/gzip, z0–14, 266 MB.
- Layers (OpenMapTiles schema):
  `boundary, building, housenumber, landcover, landuse, place, poi, transportation,
   transportation_name, water, water_name, waterway, aeroway, aerodrome_label, mountain_peak`
- Bounds: `60.821684, 23.376297 → 77.224272, 37.106671`.
- **Water polygons:** the canonical OSM water host (`osmdata.openstreetmap.de`) is unreachable
  from this network, so ocean polygons were generated from **Natural Earth 10m ocean**, projected
  to EPSG:3857 with `scripts/make_water_polygons.py`, and passed via `--water_polygons_path`.
  Coastline is therefore NE‑10m accuracy (slightly coarse).

Rebuild command (from `G:\sketcyshitx2`):

```powershell
java -Xmx6g -jar tools\planetiler.jar `
  --osm-path=data\pakistan-latest.osm.pbf `
  --output=data\pakistan_vector.pmtiles `
  --maxzoom=14 --force `
  --water_polygons_path=data\sources\water_polygons\water_polygons.zip
```

Natural Earth + lake centerlines must exist in `data\sources\` (downloaded once).

---

## 4. POI vector tiles (Overture)

**File:** `data/pakistan_places.pmtiles` → `android-assets/pakistan_places.pmtiles`

- Source: Overture places theme, release `2026-10-21.0`, 16 Parquet files.
- Extracted with **DuckDB** (`httpfs` + `spatial`), using `ST_AsMVT` / `ST_AsMVTGeom`.
- Filter: `names.primary IS NOT NULL AND confidence >= 0.5` inside the Pakistan bbox.
- **809,824 places**, z11–14, **119,921 tiles**, layer **`place`**, 214.5 MB.
- Fields per place: `name`, `cat` (detailed), `bcat` (broad), `phone`, `website`, `addr`, `status`, `conf`.
- Tiles written to MBTiles with **TMS y‑flip** (`tile_row = 2^z-1-y`), then `pmtiles convert`.

Rebuild: `python scripts\build_overture_pois.py` then `pmtiles convert`.

DuckDB gotchas learned the hard way:
- S3 `glob()` is flaky → enumerate the 16 keys via the HTTPS list API (parent prefix
  `.../theme=places/`), cache them in `data/overture/places_files.json` (utf‑8‑sig).
- `ST_AsMVTGeom` wants `BOX_2D` → use `ST_Extent(ST_TileEnvelope(z,x,y))`.
- Use `PI()` not `pi`; cast tile `x/y` to `INTEGER`; use `octet_length()` for BLOB size.

---

## 5. Offline search index

**File:** `data/places_search.db` → `android-assets/places_search.db` (104.4 MB)

- SQLite **FTS5**, built from the same DuckDB `places` table.
- Schema:
  ```sql
  CREATE TABLE places (id INTEGER PRIMARY KEY, name TEXT, cat TEXT, bcat TEXT, lon REAL, lat REAL);
  CREATE VIRTUAL TABLE places_fts USING fts5(name, content='places', content_rowid='id',
      tokenize='unicode61 remove_diacritics 2');
  ```
- Query (prefix/ranked):
  ```sql
  SELECT p.name, p.cat, p.bcat, p.lon, p.lat
  FROM places_fts f JOIN places p ON p.id = f.rowid
  WHERE places_fts MATCH ?      -- e.g. 'pims*'
  ORDER BY rank LIMIT 25;
  ```
- Build: `python scripts\build_search_index.py` (3 s).
- Preview API: `python scripts\serve_search.py` → `http://127.0.0.1:8084/search?q=...`

---

## 6. Styles, themes, languages

**Files:** `data/style_{light,dark,field}.json` (+ `_ur`, `_both`), copied to
`android-assets/styles/` with `pmtiles://...` sources.

- **47 layers each**, generated by `scripts/make_styles_pretty.py`, then the POI layer injected by
  `scripts/add_places_layer.py`, then `_ur`/`_both` variants by `scripts/make_urdu_styles.py`.
- Two sources:
  ```json
  "v":      { "type": "vector", "url": "pmtiles://pakistan_vector.pmtiles" },
  "places": { "type": "vector", "url": "pmtiles://pakistan_places.pmtiles" }
  ```
- `sprite`: `assets/sprite/sprite` · `glyphs`: `assets/fonts/{fontstack}/{range}.pbf`.

Layer set (order): background; landcover (wood/grass/farm); landuse (residential/commercial/
industrial/cemetery/hospital/school); park; water; waterway; aeroway; building; building‑3d
(z16+ fill‑extrusion); boundary; roads by class with casings (motorway→trunk→primary→secondary→
tertiary→minor); service/track; paths; rail; **road‑bridge**; **road‑tunnel**; **transit‑line**;
**oneway arrows** (z16+); road labels; **road shields** (`ref` → `road_1..6` sprite); water names;
aerodrome; peaks; place village/town/**suburb**/city; **housenumber** (z16+); **places** (POIs).

Theme palettes: light (Google‑like beige/white/yellow/orange), dark, and **field** (black +
amber, high contrast). Urdu uses `name:ur`; `_both` uses a `format` expression stacking
English + Urdu.

---

## 7. Offline assets

`data/assets/` (copied into the bundle):

- `maplibre-gl.js` / `maplibre-gl.css` (4.7.1), `pmtiles.js` (3.2.1)
- `sprite/sprite.json|png|@2x.*` (OSM Bright sprite, 103 icons)
- `fonts/Noto Sans Regular|Medium|Italic/` — **all 256 glyph ranges** (0–65535).

**Critical:** the full 256 ranges are required. A missing range makes that tile's symbol bucket
fail and the **whole tile disappears** (this was the earlier “missing blocks” bug). Do not ship a
partial glyph set. `Noto Sans Bold` is not on the CDN — don't reference it.

---

## 8. Preview environment (dev only)

Start these before opening the viewers:

| Port | Process | Purpose |
|---|---|---|
| 8001 | `python -m http.server --directory data` | viewers + assets |
| 8080 | `tools\pmtiles.exe serve data --interface 127.0.0.1 --port 8080 --public-url http://localhost:8080 --cors=*` | ZXY tiles |
| 8082 | `python scripts\serve_range.py 8082` | Range server for direct `.pmtiles` |
| 8083 | `python scripts\serve_proxy.py 8083` | strips 304s, empty tiles for 404, decompresses gzip |
| 8084 | `python scripts\serve_search.py 8084` | FTS search API |

Viewers:
- `http://localhost:8001/themed_viewer.html` — Light/Dark/Field, EN/اردو/both, nearest‑amenity,
  category chips, **search autocomplete**, clickable POIs.
- `http://localhost:8001/nav_viewer.html` — navigation demo: 3D pitch, route casing/line/arrows,
  destination pin, HUD, speed limit, Drive simulation.
- `http://localhost:8001/viewer.html` — old raster viewer (legacy).

The proxy/304 workarounds are **browser‑preview only**; an Android PMTiles reader does not need
them.

---

## 9. Waffle integration — current app state

Repo: `D:\Waffle` — Kotlin/Compose, MapLibre Native **11.8.0**, GraphHopper 1.0, Room,
WorkManager.

Relevant code:

- `app/src/main/java/com/noobdev/waffle/feature/map/MapStyles.kt`
  - `MapStyleResolver.resolve(context, index)` — online MapTiler/OpenFreeMap styles; offline
    MapTiler regions.
  - `MapStyleResolver.localPmtilesStyle(context)` — looks for
    `pakistan_protomaps.pmtiles`, `pakistan.pmtiles`, `rawalpindi.pmtiles` in
    `getExternalFilesDir(null)` / `filesDir`, builds `pmtiles://file://<path>`, and loads
    `assets/protomaps_style.json` or `assets/pakistan_style.json`, replacing
    `__PMTILES__`, `__GLYPHS__`, `__SPRITE__`.
  - Inline fallback: dark, label‑less OpenMapTiles style (source `base`).
  - `LocationAwareMap` uses the local PMTiles **only when offline and no MapTiler region**.
- `assets/pakistan_style.json` and `assets/protomaps_style.json` are **Protomaps schema**
  (`roads`, `earth`, `water`, `places`) — NOT OpenMapTiles. Our archive is OpenMapTiles, so a
  **new style** is required; do not point our archive at those templates.
- Other map pieces: `MapScreen.kt` (huge), `MapShops`, `MapSearch`, `RoutePreview`,
  `NavigationModeUI`, `Puck3D`, `OfflineMapManager`, `assets/offline_places.tsv`,
  `assets/graph-cache/` (GraphHopper), flood data.
- Note in the map README: **do not casually upgrade MapLibre** (offline region metadata is
  version‑sensitive).

### Integration plan (recommended)

1. Copy into `context.getExternalFilesDir(null)`:
   `pakistan_vector.pmtiles`, `pakistan_places.pmtiles`, `places_search.db`.
2. Copy `assets/fonts/` → `<files>/fonts/`, `assets/sprite/` → `<files>/style/`.
3. Add our styles to `app/src/main/assets/` as e.g. `waffle_vector_light.json` (and dark/field/
   ur/both) with placeholders `__PMTILES__`, `__PLACES__`, `__GLYPHS__`, `__SPRITE__`.
4. Add `localVectorStyle(context, theme, lang)` to `MapStyleResolver`:
   - detect `pakistan_vector.pmtiles`;
   - inject `pmtiles://file://...` for both archives, `file://.../fonts/{fontstack}/{range}.pbf`,
     `file://.../style/sprite`;
   - return the JSON string → `Style.Builder().fromJson(...)`.
5. Prefer the local vector style for Pakistan (online **and** offline); keep MapTiler/
   OpenFreeMap as global fallback. This removes MapTiler 429s and the label‑less fallback.
6. POI tap: `map.queryRenderedFeatures(point, "places")` → detail sheet (name, cat, phone,
   address) → **Directions** → GraphHopper.
7. Nearest amenity: `map.querySourceFeatures("places", QuerySourceFeaturesOptions().sourceLayer("place"))`
   + distance to the user.
8. Search: query `places_search.db` (FTS5) via Room/SQLite; no server needed.
9. Navigation: feed GraphHopper polyline into route layers; reuse the visual system from
   `nav_viewer.html` (casing → line → arrows, 3D pitch, HUD, speed limit).

Two `pmtiles://` sources are supported by MapLibre Native 11.8.0.

---

## 10. Gotchas / hard‑won knowledge

- **Glyph ranges:** bundle all 256 per font, or tiles disappear.
- **maxzoom 14 + overzoom:** never request z15+ tiles from a server; MapLibre overzooms z14.
- **Google raster tiles are pictures**, not data. Amenities come from OSM + Overture.
- **Water polygons:** canonical OSM host IP‑blocked here; ocean from NE 10m (coarse).
- **Urdu font:** Protomaps `Noto Sans Regular` includes Arabic/Urdu glyphs; no extra font needed.
- **S3 glob** is flaky; use the cached explicit file list (`places_files.json`).
- **DuckDB MVT:** `ST_Extent(ST_TileEnvelope(...))`, `PI()`, integer tile coords.
- **Browser preview caching:** use a cache‑buster on style/tile URLs; the debug browser mishandles
  304s. The proxy (8083) fixes 304/404.
- **SQLite FTS5 external content** requires `'rebuild'` after inserts.
- **MapLibre `querySourceFeatures`** needs `sourceLayer: "place"` (returns 0 otherwise).
- **MapLibre `in` with arrays** needs `["literal", [...]]`; `["in", get, ["a","b"]]` fails.
  `text-field` should be coerced with `["to-string", ...]`.
- **POI overload:** 809k places at z11–13 can be dense; the `places` layer uses
  `text-optional`, `icon-allow-overlap: false`, and category filters to keep it readable.

---

## 11. Rebuild / regenerate

All scripts in `G:\sketcyshitx2\scripts\`:

| Script | Purpose |
|---|---|
| `make_water_polygons.py` | NE ocean → EPSG:3857 water_polygons shapefile |
| `build_overture_pois.py` | Overture → POI MBTiles (DuckDB) |
| `build_search_index.py` | DuckDB places → SQLite FTS5 |
| `make_styles_pretty.py` | generate light/dark/field (47 layers) |
| `add_places_layer.py` | inject Overture `places` layer into styles (dev + Android) |
| `make_urdu_styles.py` | generate `_ur` / `_both` variants |
| `fetch_fonts.py` | download all 256 glyph ranges |
| `package_android.py` | build `android-assets/` |
| `serve_proxy.py` / `serve_range.py` / `serve_search.py` | dev servers |
| `fetch_tiles_fast.py` / `tiles_to_mbtiles_fast.py` | legacy raster pipeline |

Final build order after a style change:
```
python scripts\make_styles_pretty.py
python scripts\package_android.py
python scripts\add_places_layer.py
python scripts\make_urdu_styles.py
```

---

## 12. Licensing / attribution

- OSM data: **ODbL 1.0** — attribution `© OpenStreetMap contributors`.
- OpenMapTiles schema/produced work: **CC‑BY** — attribution `© OpenMapTiles`.
- Overture Places: **CDLA‑Permissive 2.0** — attribution `© Overture Maps Foundation`.
- Do not ship data extracted from the Google app; it is proprietary and unlicensed for
  redistribution.

---

## 13. Open items / next

1. Wire the stack into Waffle (`localVectorStyle` + PMTiles + FTS search).
2. POI category filters + nearest search inside Waffle's UI.
3. Route‑aware POIs (fuel/food/hospital along the GraphHopper route).
4. Optional: Overture `addresses`/`transportation` themes, GTFS transit, DEM hillshade/contours,
   real building heights, per‑network shields.
5. Consider a “lite” POI variant without phone/website/address (~97 MB vs 214 MB).
