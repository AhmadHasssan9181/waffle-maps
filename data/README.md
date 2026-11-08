# Large data artifacts

GitHub blocks files larger than 100 MB from a normal repository, so the three big
artifacts are attached to the **[latest release](https://github.com/AhmadHasssan9181/waffle-maps/releases/latest)**.

Download them into this `data/` folder:

| File | Size | Purpose |
|---|---:|---|
| `pakistan_vector.pmtiles` | 266 MB | Basemap vector tiles (z0–14, OpenMapTiles) |
| `pakistan_places.pmtiles` | 214.5 MB | 809,824 POIs (z11–14, layer `place`) |
| `places_search.db` | 104.4 MB | SQLite FTS5 search index |

Verify after download:

```bash
pmtiles verify pakistan_vector.pmtiles
pmtiles verify pakistan_places.pmtiles
sqlite3 places_search.db "SELECT count(*) FROM places;"   # -> 809824
```

Serving them locally for the web preview:

```bash
pmtiles serve . --port 8080
python ../scripts/serve_proxy.py 8083
python ../scripts/serve_search.py 8084
python ../scripts/serve_range.py 8082
```

Expected endpoints:

- `http://localhost:8080/pakistan_vector/{z}/{x}/{y}.mvt`
- `http://localhost:8080/pakistan_places/{z}/{x}/{y}.mvt`
- `http://localhost:8084/search?q=pims`
