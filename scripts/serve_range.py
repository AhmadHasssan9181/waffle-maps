"""Minimal static file server with HTTP Range support + CORS (for PMTiles JS)."""
import os, re, sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer


class RangeHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Access-Control-Expose-Headers", "Content-Range, Content-Length, Accept-Ranges")
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def do_GET(self):
        path = self.translate_path(self.path)
        if os.path.isfile(path):
            rng = self.headers.get("Range")
            size = os.path.getsize(path)
            if rng:
                m = re.match(r"bytes=(\d+)-(\d*)", rng)
                if m:
                    start = int(m.group(1))
                    end = int(m.group(2)) if m.group(2) else size - 1
                    end = min(end, size - 1)
                    if start <= end:
                        self.send_response(206)
                        self.send_header("Content-Type", "application/octet-stream")
                        self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
                        self.send_header("Content-Length", str(end - start + 1))
                        self.end_headers()
                        with open(path, "rb") as f:
                            f.seek(start)
                            self.wfile.write(f.read(end - start + 1))
                        return
        return super().do_GET()


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8082
    os.chdir(r"G:\sketcyshitx2\data")
    print(f"serving {os.getcwd()} on http://127.0.0.1:{port} with Range")
    ThreadingHTTPServer(("127.0.0.1", port), RangeHandler).serve_forever()
