from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import subprocess

class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(length)
            data = json.loads(body.decode("utf-8"))
        except Exception:
            self.send_response(400)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"ok":false,"error":"invalid json"}')
            return

        url = data.get("url")
        if not url:
            self.send_response(400)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"ok":false,"error":"missing url"}')
            return

        result = subprocess.run(
            ["/app/scripts/run_pipeline.sh", url],
            capture_output=True,
            text=True
        )

        stdout = (result.stdout or "").strip()
        stderr = (result.stderr or "").strip()

        if result.returncode != 0:
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            payload = {
                "ok": False,
                "error": "pipeline failed",
                "returncode": result.returncode,
                "stdout": stdout,
                "stderr": stderr,
            }
            self.wfile.write(json.dumps(payload).encode("utf-8"))
            return

        try:
            parsed = json.loads(stdout)
        except Exception:
            parsed = {
                "ok": False,
                "error": "invalid pipeline json",
                "stdout": stdout,
                "stderr": stderr,
            }

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(parsed).encode("utf-8"))

server = HTTPServer(("0.0.0.0", 9000), Handler)
server.serve_forever()
