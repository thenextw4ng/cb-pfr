"""Local CB-PFR HTML workstation server; serves checked-in evidence only."""
from __future__ import annotations

import csv
import hashlib
import json
import mimetypes
import zipfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
WEB_ROOT = ROOT / "web"
CANDIDATE_CSV = ROOT / "results" / "c5g7_layout_smoke_2026-10-10" / "candidate_summary.csv"
STATEPOINT_ARCHIVE = ROOT / "OpenMC_HDF5_Evidence_2026-10-11.zip"
STATEPOINT_MEMBER = "c5g7-run/2d/statepoint.20000.h5"
STATEPOINT_BASELINE = ROOT / "evidence" / "openmc_local_baseline_2026-10-11" / "statepoint_summary.json"


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


def read_mesh_evidence():
    """Read only the known production member from the committed statepoint archive."""
    if not STATEPOINT_ARCHIVE.is_file():
        raise FileNotFoundError(f"Statepoint archive not found: {STATEPOINT_ARCHIVE.name}")
    try:
        import h5py
        import numpy as np
    except ImportError as exc:
        raise RuntimeError("Spatial field visualization needs h5py and numpy. Install project requirements with: python -m pip install -r requirements.txt") from exc

    with zipfile.ZipFile(STATEPOINT_ARCHIVE) as archive:
        matches = [name for name in archive.namelist() if name == STATEPOINT_MEMBER]
        if len(matches) != 1:
            raise ValueError(f"Expected exactly one {STATEPOINT_MEMBER} entry, found {len(matches)}.")
        raw_bytes = archive.read(matches[0])
    actual_hash = hashlib.sha256(raw_bytes).hexdigest()
    expected_hash = None
    if STATEPOINT_BASELINE.is_file():
        baseline = json.loads(STATEPOINT_BASELINE.read_text(encoding="utf-8"))
        expected_hash = baseline.get("statepoint_file_sha256")
    records = []
    with h5py.File(__import__("io").BytesIO(raw_bytes), "r") as handle:
        tallies = handle.get("tallies")
        if tallies is None:
            raise ValueError("Statepoint HDF5 does not contain a tallies group.")
        meshes = []
        if "meshes" in tallies:
            for name, mesh in tallies["meshes"].items():
                if "dimension" not in mesh:
                    continue
                dims = [int(v) for v in np.asarray(mesh["dimension"][()]).reshape(-1)]
                if len(dims) == 3 and dims[2] == 1:
                    meshes.append((name, dims))
        for tally_name, tally in tallies.items():
            if not tally_name.startswith("tally ") or not hasattr(tally, "keys"):
                continue
            if "results" not in tally or "score_bins" not in tally:
                continue
            scores = []
            for value in np.asarray(tally["score_bins"][()]).reshape(-1):
                if isinstance(value, bytes):
                    scores.append(value.decode("utf-8", errors="replace").rstrip("\x00"))
                elif hasattr(value, "item"):
                    item = value.item()
                    scores.append(item.decode("utf-8", errors="replace").rstrip("\x00") if isinstance(item, bytes) else str(item))
                else:
                    scores.append(str(value))
            values = np.asarray(tally["results"][()])
            if values.ndim == 4 and values.shape[1] == 1:
                values = values[:, 0, :, :]
            if values.ndim != 3 or values.shape[-1] != 2 or values.shape[-2] != len(scores):
                continue
            bins = values.shape[0]
            matching = next((m for m in meshes if int(np.prod(m[1])) == bins), None)
            if matching is None:
                continue
            mesh_name, dims = matching
            if dims[0] * dims[1] != bins:
                continue
            mean_grid = {}
            sd_grid = {}
            mean_values = np.asarray(values[:, :, 0], dtype=float)
            std_values = np.asarray(values[:, :, 1], dtype=float)
            for idx, score in enumerate(scores):
                mean_grid[score] = mean_values[:, idx].reshape((dims[1], dims[0])).tolist()
                sd_grid[score] = std_values[:, idx].reshape((dims[1], dims[0])).tolist()
            records.append({"tally_name": tally_name, "mesh_name": mesh_name, "dimensions": dims, "scores": {score: {"mean": mean_grid[score], "std_dev": sd_grid[score]} for score in scores}})
    if not records:
        raise ValueError("No compatible 2-D OpenMC mesh tally found in archived statepoint.")
    return {
        "mesh_tallies": records,
        "provenance": {
            "source": "Repository archive · " + STATEPOINT_MEMBER,
            "sha256": actual_hash,
            "expected_sha256": expected_hash,
            "hash_matches": actual_hash == expected_hash if expected_hash else None,
            "evidence_status": "recorded statepoint; no geometry-to-material mapping inferred",
        },
    }


class Handler(BaseHTTPRequestHandler):
    server_version = "CBPFRLocal/0.2"

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
                payload = {"metadata": {"source": str(CANDIDATE_CSV.relative_to(ROOT)), "mode": "recorded repository evidence; no OpenMC execution"}, "records": read_candidates()}
                return self._send(200, json.dumps(payload, allow_nan=False), "application/json; charset=utf-8")
            except (OSError, ValueError, csv.Error) as exc:
                return self._send(503, json.dumps({"error": str(exc)}), "application/json; charset=utf-8")
        if path == "/api/mesh":
            try:
                return self._send(200, json.dumps(read_mesh_evidence(), allow_nan=False), "application/json; charset=utf-8")
            except (OSError, ValueError, RuntimeError, zipfile.BadZipFile, KeyError) as exc:
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
    print("Evidence mode: archived OpenMC statepoint + checked-in candidate summary; no OpenMC execution.")
    ThreadingHTTPServer((host, port), Handler).serve_forever()
