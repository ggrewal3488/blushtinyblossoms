import http.server, os, sys
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), "dist"))
class H(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        p = self.path.split("?")[0]
        if p != "/" and "." not in p.rsplit("/", 1)[-1]:
            if os.path.exists(p.lstrip("/") + ".html"): self.path = p + ".html"
            else:
                self.send_response(404); self.send_header("Content-Type", "text/html"); self.end_headers(); self.wfile.write(open("404.html", "rb").read()); return
        return super().do_GET()
    def log_message(self, *a): pass
http.server.ThreadingHTTPServer(("127.0.0.1", 8123), H).serve_forever()
