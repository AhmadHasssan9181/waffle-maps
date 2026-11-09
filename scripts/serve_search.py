"""Offline POI search API over the SQLite FTS5 index."""
import http.server, json, sqlite3, sys, urllib.parse

DB = r"G:\sketcyshitx2\data\places_search.db"


class Handler(http.server.BaseHTTPRequestHandler):
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Cache-Control", "no-store")

    def _json(self, data):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self._cors()
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        if u.path != "/search":
            self.send_error(404)
            return
        q = urllib.parse.parse_qs(u.query).get("q", [""])[0].strip()
        if not q:
            self._json([])
            return
        match = " ".join(t.replace('"', "") + "*" for t in q.split() if t)
        try:
            con = sqlite3.connect(DB)
            con.row_factory = sqlite3.Row
            rows = con.execute(
                """SELECT p.name, p.name_ur, p.cat, p.bcat, p.lon, p.lat
                   FROM places_fts f JOIN places p ON p.id = f.rowid
                   WHERE places_fts MATCH ? ORDER BY rank LIMIT 25""",
                (match,),
            ).fetchall()
            con.close()
            self._json([dict(r) for r in rows])
        except Exception as e:
            self._json({"error": str(e)})

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8084
    print(f"search API on http://127.0.0.1:{port}/search?q=...")
    http.server.ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()
