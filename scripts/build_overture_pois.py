import json, os, sqlite3, time
import duckdb

REL = "2026-10-21.0"
PREFIX = f"release/{REL}/theme=places/type/place/"
WORK = r"G:\sketcyshitx2\data\overture"
os.makedirs(WORK, exist_ok=True)
MBT = os.path.join(WORK, "pakistan_places.mbtiles")

with open(os.path.join(WORK, "places_files.json"), encoding="utf-8-sig") as f:
    keys = json.load(f)
files = ["s3://overturemaps-us-west-2/" + k for k in keys]
print("source files:", len(files), flush=True)

con = duckdb.connect(os.path.join(WORK, "overture.duckdb"))
con.execute("INSTALL httpfs; LOAD httpfs;")
con.execute("INSTALL spatial; LOAD spatial;")
con.execute("SET s3_region='us-west-2';")
con.execute("SET threads=12;")

t = time.time()
con.execute(f"""
CREATE OR REPLACE TABLE places AS
SELECT names.primary AS name,
       COALESCE(taxonomy.primary, basic_category, 'place') AS cat,
       COALESCE(basic_category, 'place') AS bcat,
       phones[1] AS phone,
       websites[1] AS website,
       COALESCE(addresses[1].freeform, addresses[1].locality, '') AS addr,
       operating_status AS status,
       confidence AS conf,
       bbox.xmin AS lon, bbox.ymin AS lat,
       geometry AS geom
FROM read_parquet({files!r})
WHERE names.primary IS NOT NULL
  AND confidence >= 0.5
  AND bbox.xmin BETWEEN 60.8 AND 77.3
  AND bbox.ymin BETWEEN 23.3 AND 37.2
""")
n = con.execute("SELECT count(*) FROM places").fetchone()[0]
print(f"places: {n}  ({time.time()-t:.0f}s)", flush=True)

if os.path.exists(MBT):
    os.remove(MBT)
db = sqlite3.connect(MBT)
cur = db.cursor()
cur.execute("PRAGMA journal_mode=OFF")
cur.execute("PRAGMA synchronous=OFF")
cur.execute("CREATE TABLE metadata (name TEXT, value TEXT)")
cur.execute("CREATE TABLE tiles (zoom_level INTEGER, tile_column INTEGER, tile_row INTEGER, tile_data BLOB)")
cur.execute("CREATE UNIQUE INDEX tile_index ON tiles (zoom_level, tile_column, tile_row)")
cur.executemany("INSERT INTO metadata VALUES (?,?)", [
    ("name", "Pakistan Places (Overture)"), ("format", "pbf"),
    ("minzoom", "11"), ("maxzoom", "14"),
    ("bounds", "60.8,23.3,77.3,37.2"), ("type", "overlay"), ("version", "1"),
    ("description", "Named places from Overture Maps"),
    ("attribution", "© Overture Maps Foundation"),
])

for z in range(11, 15):
    t = time.time()
    rows = con.execute(f"""
      WITH p AS (
        SELECT name, cat, bcat, phone, website, addr, status, geom,
               CAST(floor((lon + 180) / 360 * {2**z}) AS INTEGER) AS x,
               CAST(floor((1 - ln(tan(radians(lat)) + 1/cos(radians(lat))) / PI()) / 2 * {2**z}) AS INTEGER) AS y
        FROM places
      )
      SELECT x, y, tile
      FROM (
        SELECT x, y, ST_AsMVT(t, 'place', 4096, 'geom') AS tile
        FROM (
          SELECT x, y,
                 ST_AsMVTGeom(ST_Transform(geom, 'EPSG:4326', 'EPSG:3857', always_xy := true),
                              ST_Extent(ST_TileEnvelope({z}, x, y)), 4096, 64, true) AS geom,
                 name, cat, bcat, phone, website, addr, status
          FROM p
        ) t
        GROUP BY x, y
      )
    """).fetchall()
    for x, y, tile in rows:
        cur.execute("INSERT OR REPLACE INTO tiles VALUES (?,?,?,?)", (z, x, (2 ** z - 1) - y, tile))
    db.commit()
    print(f"z{z}: {len(rows)} tiles  ({time.time()-t:.0f}s)", flush=True)

db.close()
print("mbtiles MB:", round(os.path.getsize(MBT) / 1e6, 1), flush=True)
