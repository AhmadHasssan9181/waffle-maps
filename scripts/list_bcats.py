import duckdb

con = duckdb.connect(r"G:\sketcyshitx2\data\overture\overture.duckdb")
for n, cat in con.execute(
        "SELECT count(*) c, bcat FROM places GROUP BY bcat ORDER BY c DESC LIMIT 80").fetchall():
    print(f"{n:>8}  {cat}")
