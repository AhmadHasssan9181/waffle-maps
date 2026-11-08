## W.A.F.F.L.E. Maps v1.0.0

Offline vector map stack for Pakistan — part of Project W.A.F.F.L.E.

### Assets

- **pakistan_vector.pmtiles** — basemap z0–14, MVT/gzip, OpenMapTiles schema (266 MB)
- **pakistan_places.pmtiles** — 809,824 places, z11–14, layer `place` (214.5 MB)
- **places_search.db** — SQLite FTS5 search index (104.4 MB)

### Verify

```bash
pmtiles verify pakistan_vector.pmtiles
pmtiles verify pakistan_places.pmtiles
sqlite3 places_search.db "SELECT count(*) FROM places;"   # 809824
```

### Attribution

© OpenMapTiles · © OpenStreetMap contributors · © Overture Maps Foundation
