"""Local preview:  python3 serve.py  → http://127.0.0.1:8123/   (add a path prefix as argument to mimic username.github.io/repo/)"""
import http.server, os, sys
DOCS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs")
PREFIX = "/" + sys.argv[1].strip("/") if len(sys.argv) > 1 else ""
class H(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k): super().__init__(*a, directory=DOCS, **k)
    def do_GET(self):
        p = self.path.split("?")[0]
        if PREFIX:
            if not p.startswith(PREFIX + "/"): self.send_error(404); return
            p = p[len(PREFIX):]
        self.path = p
        if p != "/" and not p.endswith("/") and "." not in p.rsplit("/", 1)[-1]:
            if os.path.exists(os.path.join(DOCS, p.lstrip("/") + ".html")): self.path = p + ".html"
            else:
                self.send_response(404); self.send_header("Content-Type", "text/html"); self.end_headers()
                self.wfile.write(open(os.path.join(DOCS, "404.html"), "rb").read()); return
        return super().do_GET()
    def log_message(self, *a): pass
http.server.ThreadingHTTPServer(("127.0.0.1", int(os.environ.get("PORT", 8123))), H).serve_forever()
