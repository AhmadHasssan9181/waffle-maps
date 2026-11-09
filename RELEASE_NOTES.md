## W.A.F.F.L.E. Maps v1.0.0

Offline vector map stack for Pakistan — part of Project W.A.F.F.L.E.

### Assets

- **pakistan_vector.pmtiles** — basemap z0–14, MVT/gzip, OpenMapTiles schema, `name:ur` filled (276.9 MB)
- **pakistan_places.pmtiles** — 809,824 places, z11–14, layer `place`, `name:ur` filled (274.7 MB)
- **places_search.db** — SQLite FTS5 search index over `name` + `name_ur` (153.5 MB)

> **Updated 2026-11-09:** both PMTiles now carry `name:ur` for every labelled feature
> (OSM tag where present, build-time transliteration otherwise), and the search
> index is bilingual. The `*_ur` and `*_both` styles are fully Urdu.

### Verify

```bash
pmtiles verify pakistan_vector.pmtiles
pmtiles verify pakistan_places.pmtiles
sqlite3 places_search.db "SELECT count(*) FROM places;"   # 809824
```

### Attribution

© OpenMapTiles · © OpenStreetMap contributors · © Overture Maps Foundation
