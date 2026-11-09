"""Static file server for the web preview with CORS (required by MapLibre's worker)."""
import http.server, mimetypes, os, sys

mimetypes.add_type("application/wasm", ".wasm")
mimetypes.add_type("application/x-protobuf", ".pbf")
mimetypes.add_type("application/json", ".json")


class Handler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, HEAD, OPTIONS")
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8001
    root = sys.argv[2] if len(sys.argv) > 2 else r"G:\sketcyshitx2\data"
    os.chdir(root)
    print(f"serving {root} on :{port} (CORS on)")
    http.server.ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()
