"""Proxy in front of `pmtiles serve` (localhost:8080).
- strips If-None-Match / If-Modified-Since -> always fresh 200 (no 304 gaps)
- 404 (tile not in archive) -> 200 empty MVT (renders as empty, not a hole/error)
- adds CORS + no-store
"""
import gzip, http.server, sys, urllib.error, urllib.request

UPSTREAM = "http://127.0.0.1:8080"


class Handler(http.server.BaseHTTPRequestHandler):
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Cache-Control", "no-store")

    def do_GET(self):
        hdrs = {k: v for k, v in self.headers.items()
                if k.lower() not in ("host", "if-none-match", "if-modified-since", "range")}
        try:
            req = urllib.request.Request(UPSTREAM + self.path, headers=hdrs)
            with urllib.request.urlopen(req, timeout=30) as r:
                data = r.read()
                enc = r.headers.get("Content-Encoding")
            if enc == "gzip":
                try:
                    data = gzip.decompress(data)
                except Exception:
                    pass
            self.send_response(200)
            self.send_header("Content-Type", r.headers.get("Content-Type", "application/octet-stream"))
            self.send_header("Content-Length", str(len(data)))
            self._cors()
            self.end_headers()
            self.wfile.write(data)
        except urllib.error.HTTPError as e:
            if e.code in (404, 204):
                self.send_response(200)
                self.send_header("Content-Type", "application/x-protobuf")
                self.send_header("Content-Length", "0")
                self._cors()
                self.end_headers()
            else:
                self.send_error(e.code)
        except Exception:
            self.send_response(200)
            self.send_header("Content-Type", "application/x-protobuf")
            self.send_header("Content-Length", "0")
            self._cors()
            self.end_headers()

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8083
    print(f"proxy -> {UPSTREAM} on :{port}")
    http.server.ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()
