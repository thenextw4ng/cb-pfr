"""Local CB-PFR HTML workstation server; serves repository-recorded data only."""
from __future__ import annotations

import csv
import json
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
WEB_ROOT = ROOT / "web"
CANDIDATE_CSV = ROOT / "results" / "c5g7_layout_smoke_2026-10-10" / "candidate_summary.csv"


def read_candidates():
    if not CANDIDATE_CSV.is_file():
        raise FileNotFoundError(f"Candidate summary not found: {CANDIDATE_CSV.relative_to(ROOT)}")
    with CANDIDATE_CSV.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError("Candidate summary CSV has no header row.")
        rows = []
        for raw in reader:
            row = {}
            for key, value in raw.items():
                if value is None or value.strip() == "":
                    row[key] = None
                    continue
                try:
                    row[key] = float(value) if any(ch in value.lower() for ch in (".", "e")) else int(value)
                except (ValueError, AttributeError):
                    row[key] = value
            rows.append(row)
    return rows


class Handler(BaseHTTPRequestHandler):
    server_version = "CBPFRLocal/0.1"

    def _send(self, status, body, content_type):
        payload = body.encode("utf-8") if isinstance(body, str) else body
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/health":
            return self._send(200, json.dumps({"status": "ok", "mode": "recorded-evidence-only"}), "application/json; charset=utf-8")
        if path == "/api/candidates":
            try:
                records = read_candidates()
                payload = {"metadata": {"source": str(CANDIDATE_CSV.relative_to(ROOT)), "record_count": len(records), "mode": "recorded repository evidence; no OpenMC execution"}, "records": records}
                return self._send(200, json.dumps(payload, allow_nan=False), "application/json; charset=utf-8")
            except (OSError, ValueError, csv.Error) as exc:
                return self._send(503, json.dumps({"error": str(exc)}), "application/json; charset=utf-8")
        routes = {"/": WEB_ROOT / "index.html", "/index.html": WEB_ROOT / "index.html", "/styles.css": WEB_ROOT / "styles.css", "/app.js": WEB_ROOT / "app.js"}
        file_path = routes.get(path)
        if file_path is None:
            return self._send(404, "Not found", "text/plain; charset=utf-8")
        try:
            content = file_path.read_bytes()
        except OSError:
            return self._send(500, "Frontend asset missing: " + file_path.name, "text/plain; charset=utf-8")
        content_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
        if content_type.startswith("text/") or content_type in ("application/javascript",):
            content_type += "; charset=utf-8"
        return self._send(200, content, content_type)

    def log_message(self, fmt, *args):
        print("[CB-PFR]", fmt % args)


if __name__ == "__main__":
    host, port = "127.0.0.1", 8765
    print(f"CB-PFR HTML workstation: http://{host}:{port}")
    print("Evidence mode: checked-in candidate summary only; OpenMC is not launched.")
    ThreadingHTTPServer((host, port), Handler).serve_forever()
