import os, sqlite3, time
import duckdb

SRC = r"G:\sketcyshitx2\data\overture\overture.duckdb"
OUT = r"G:\sketcyshitx2\data\places_search.db"

if os.path.exists(OUT):
    os.remove(OUT)

dcon = duckdb.connect(SRC)
dcon.execute("SET threads=8")

db = sqlite3.connect(OUT)
db.execute("PRAGMA journal_mode=OFF")
db.execute("PRAGMA synchronous=OFF")
db.execute("PRAGMA cache_size=-200000")
db.execute("CREATE TABLE places (id INTEGER PRIMARY KEY, name TEXT, cat TEXT, bcat TEXT, lon REAL, lat REAL)")
db.execute("""CREATE VIRTUAL TABLE places_fts USING fts5(
                 name, content='places', content_rowid='id',
                 tokenize='unicode61 remove_diacritics 2')""")

cur = dcon.execute("SELECT name, cat, bcat, lon, lat FROM places")
i = 0
t = time.time()
batch = []
while True:
    rows = cur.fetchmany(20000)
    if not rows:
        break
    for r in rows:
        i += 1
        batch.append((i, r[0], r[1], r[2], r[3], r[4]))
    db.executemany("INSERT INTO places VALUES (?,?,?,?,?,?)", batch)
    db.commit()
    batch.clear()
    print(i, f"{time.time()-t:.0f}s", flush=True)

print("building FTS...", flush=True)
db.execute("INSERT INTO places_fts(places_fts) VALUES('rebuild')")
db.execute("CREATE INDEX idx_bcat ON places(bcat)")
db.commit()
db.close()
print("done", round(os.path.getsize(OUT) / 1e6, 1), "MB", f"{time.time()-t:.0f}s", flush=True)
