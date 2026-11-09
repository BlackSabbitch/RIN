"""Transparent capture proxy: records exactly what a client (SillyTavern) sends to Ollama.

    python -m harness.capture_proxy            # listens on 127.0.0.1:11435 -> 127.0.0.1:11434

Point SillyTavern's Custom endpoint at http://127.0.0.1:11435/v1 while capturing,
then back to :11434. Every POST .../chat/completions body is saved to
harness/fixtures/parity/<timestamp>.json, after all ST processing
(prompt post-processing included). That file is the ground truth for the
prompt-parity test. Everything else is forwarded untouched, streaming included.

Captured files contain real chat text: harness/fixtures/parity/ is gitignored.
"""

from __future__ import annotations

import argparse
import json
import urllib.error
import urllib.request
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

CAPTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "parity"
HOP_HEADERS = {"connection", "keep-alive", "transfer-encoding", "content-length", "host"}


def make_handler(upstream: str):
    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, fmt, *args):  # quiet
            pass

        def _forward(self, method: str) -> None:
            length = int(self.headers.get("Content-Length") or 0)
            body = self.rfile.read(length) if length else None

            if method == "POST" and self.path.rstrip("/").endswith("/chat/completions") and body:
                CAPTURE_DIR.mkdir(parents=True, exist_ok=True)
                stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                out = CAPTURE_DIR / f"{stamp}.json"
                try:
                    parsed = json.loads(body)
                    out.write_text(json.dumps(parsed, ensure_ascii=False, indent=2), encoding="utf-8")
                    n = len(parsed.get("messages", []))
                    print(f"captured {out.name}: model={parsed.get('model')} messages={n}", flush=True)
                except json.JSONDecodeError:
                    out.with_suffix(".raw").write_bytes(body)

            headers = {k: v for k, v in self.headers.items() if k.lower() not in HOP_HEADERS}
            req = urllib.request.Request(upstream + self.path, data=body, headers=headers, method=method)
            try:
                resp = urllib.request.urlopen(req, timeout=600)
                status = resp.status
            except urllib.error.HTTPError as err:
                resp, status = err, err.code

            self.send_response(status)
            for k, v in resp.headers.items():
                if k.lower() not in HOP_HEADERS:
                    self.send_header(k, v)
            self.send_header("Transfer-Encoding", "chunked")
            self.end_headers()
            while True:
                chunk = resp.read1(8192) if hasattr(resp, "read1") else resp.read(8192)
                if not chunk:
                    break
                self.wfile.write(f"{len(chunk):x}\r\n".encode() + chunk + b"\r\n")
                self.wfile.flush()
            self.wfile.write(b"0\r\n\r\n")
            self.wfile.flush()

        def do_GET(self):
            self._forward("GET")

        def do_POST(self):
            self._forward("POST")

    return Handler


def main() -> None:
    ap = argparse.ArgumentParser(description="Capture what a client sends to Ollama.")
    ap.add_argument("--listen", type=int, default=11435)
    ap.add_argument("--upstream", default="http://127.0.0.1:11434")
    args = ap.parse_args()
    server = ThreadingHTTPServer(("127.0.0.1", args.listen), make_handler(args.upstream.rstrip("/")))
    print(f"capture proxy 127.0.0.1:{args.listen} -> {args.upstream}; saving to {CAPTURE_DIR}")
    print("Ctrl+C to stop")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
