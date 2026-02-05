#!/usr/bin/env python3
"""
Simple HTTP server that serves frontend static files and proxies /api requests to the backend.
"""

import http.server
import socketserver
import urllib.request
import urllib.error
import os
from pathlib import Path

PORT = 8080
BACKEND_URL = "http://localhost:8000"
STATIC_DIR = Path(__file__).parent / "frontend" / "dist"


class ProxyHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC_DIR), **kwargs)

    def do_GET(self):
        if self.path.startswith("/api"):
            self.proxy_request("GET")
        else:
            # For SPA routing, serve index.html for non-file paths
            file_path = STATIC_DIR / self.path.lstrip("/")
            if not file_path.exists() and not self.path.startswith("/assets"):
                self.path = "/index.html"
            super().do_GET()

    def do_POST(self):
        if self.path.startswith("/api"):
            self.proxy_request("POST")
        else:
            self.send_error(405, "Method Not Allowed")

    def do_PUT(self):
        if self.path.startswith("/api"):
            self.proxy_request("PUT")
        else:
            self.send_error(405, "Method Not Allowed")

    def do_DELETE(self):
        if self.path.startswith("/api"):
            self.proxy_request("DELETE")
        else:
            self.send_error(405, "Method Not Allowed")

    def proxy_request(self, method):
        url = f"{BACKEND_URL}{self.path}"

        # Read request body for POST/PUT
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else None

        # Build headers to forward
        headers = {}
        for header in ["Content-Type", "Authorization", "Accept"]:
            if header in self.headers:
                headers[header] = self.headers[header]

        try:
            req = urllib.request.Request(url, data=body, headers=headers, method=method)
            with urllib.request.urlopen(req) as response:
                self.send_response(response.status)
                for header, value in response.getheaders():
                    if header.lower() not in ["transfer-encoding", "connection"]:
                        self.send_header(header, value)
                self.end_headers()
                self.wfile.write(response.read())
        except urllib.error.HTTPError as e:
            self.send_response(e.code)
            self.send_header("Content-Type", e.headers.get("Content-Type", "application/json"))
            self.end_headers()
            self.wfile.write(e.read())
        except urllib.error.URLError as e:
            self.send_error(502, f"Backend unavailable: {e.reason}")

    def log_message(self, format, *args):
        print(f"[{self.log_date_time_string()}] {args[0]}")


if __name__ == "__main__":
    os.chdir(STATIC_DIR)

    with socketserver.TCPServer(("0.0.0.0", PORT), ProxyHandler) as httpd:
        print(f"Serving frontend from {STATIC_DIR}")
        print(f"Proxying /api/* to {BACKEND_URL}")
        print(f"Server running at http://0.0.0.0:{PORT}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down...")
