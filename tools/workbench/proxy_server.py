"""
IRIS Workbench proxy server.
Serves static files from this directory + proxies POST /proxy/anthropic to
api.anthropic.com server-side, bypassing browser CORS restrictions.

Replaces: python -m http.server 8080
Usage:    python proxy_server.py
"""
import http.server
import urllib.request
import urllib.error
import os

PORT = 8080
WORKBENCH_DIR = os.path.dirname(os.path.abspath(__file__))


class WorkbenchHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WORKBENCH_DIR, **kwargs)

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors_headers()
        self.end_headers()

    def do_POST(self):
        if self.path == "/proxy/anthropic":
            self._proxy_anthropic()
        else:
            self.send_error(404, "Not found")

    def _proxy_anthropic(self):
        length = int(self.headers.get("Content-Length", 0))
        body   = self.rfile.read(length)

        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=body,
            headers={
                "Content-Type":      "application/json",
                "x-api-key":         self.headers.get("x-api-key", ""),
                "anthropic-version": self.headers.get("anthropic-version", "2023-06-01"),
            },
            method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                resp_body = resp.read()
                self.send_response(resp.status)
                self.send_header("Content-Type", "application/json")
                self._cors_headers()
                self.end_headers()
                self.wfile.write(resp_body)
        except urllib.error.HTTPError as e:
            resp_body = e.read()
            self.send_response(e.code)
            self.send_header("Content-Type", "application/json")
            self._cors_headers()
            self.end_headers()
            self.wfile.write(resp_body)
        except Exception as e:
            msg = str(e).encode()
            self.send_response(502)
            self.send_header("Content-Type", "text/plain")
            self._cors_headers()
            self.end_headers()
            self.wfile.write(msg)

    def _cors_headers(self):
        self.send_header("Access-Control-Allow-Origin",  "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers",
                         "Content-Type, x-api-key, anthropic-version")

    def log_message(self, fmt, *args):
        pass  # suppress per-request log noise


if __name__ == "__main__":
    with http.server.HTTPServer(("", PORT), WorkbenchHandler) as httpd:
        print(f"IRIS Workbench running at http://localhost:{PORT}")
        print("Press Ctrl+C to stop.")
        httpd.serve_forever()
