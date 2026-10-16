#!/usr/bin/env python3
"""Build a GitHub Pages version of the CB-PFR workstation from recorded repo evidence.

The interactive workstation normally reads evidence through web_server.py. GitHub Pages
is static hosting, so this script precomputes those read-only API responses during CI and
rewrites the published copy to use same-origin JSON files. Source files in web/ are not
modified by this build.
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB_ROOT = ROOT / "web"
SITE = ROOT / "_site"
API_DIR = SITE / "api"


def write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, allow_nan=False, separators=(",", ":")),
        encoding="utf-8",
    )


def load_server_module():
    sys.path.insert(0, str(ROOT))
    import web_server  # noqa: PLC0415
    return web_server


def make_api_snapshot(server) -> None:
    """Materialize the same read-only payloads the local HTTP server supplies."""
    API_DIR.mkdir(parents=True, exist_ok=True)
    write_json(API_DIR / "health.json", {
        "status": "ok",
        "mode": "recorded-evidence-only",
        "hosting": "static-snapshot",
    })
    write_json(API_DIR / "evidence-index.json", server.read_evidence_index())
    write_json(API_DIR / "candidates.json", server.read_candidate_evidence())
    write_json(API_DIR / "model-geometry.json", server.read_model_geometry())
    write_json(API_DIR / "assembly.json", server.read_assembly_evidence())
    write_json(API_DIR / "mesh.json", server.read_mesh_evidence())

    # The UI's axial selector requests one score at a time. Build one immutable
    # snapshot per score so the selector still displays the recorded score it asks for.
    import numpy as np  # noqa: PLC0415
    with np.load(server.AXIAL_TALLY_NPZ, allow_pickle=False) as archive:
        if "score_names" not in archive.files:
            raise ValueError("Axial NPZ does not contain score_names.")
        scores = [
            item.decode("utf-8") if isinstance(item, bytes) else str(item)
            for item in archive["score_names"].tolist()
        ]
    if not scores:
        raise ValueError("Axial NPZ has no recorded tally scores.")
    for score in scores:
        safe_score = score.replace("/", "-").replace("\\", "-")
        write_json(
            API_DIR / f"axial-3d-{safe_score}.json",
            server.read_axial_3d_evidence(score),
        )

    # Geometry outputs are source artifacts, never invented by the dashboard.
    artifact_index = server.list_geometry_artifacts()
    for item in artifact_index.get("artifacts", []):
        rel = item.get("path")
        if not rel:
            continue
        source = (ROOT / rel).resolve()
        if not source.is_file() or ROOT.resolve() not in source.parents:
            raise ValueError(f"Geometry artifact path is missing or outside repository: {rel}")
        target = SITE / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        item["url"] = "./" + rel.replace("\\", "/")
    write_json(API_DIR / "geometry-artifacts.json", artifact_index)


def rewrite_for_pages() -> None:
    """Fix site-root URLs and map backend routes to generated static JSON files."""
    static_files = [
        "index.html",
        "styles.css",
        "app.js",
        "research_snapshot_ui.js",
        "evidence_control_room.js",
        "axial_investigation.js",
        "uncertainty_analysis.js",
        "figure_studio.js",
        "core_geometry_3d.js",
        "spatial.js",
        "research_snapshot.json",
    ]
    replacements = {
        'fetch("/api/model-geometry"': 'fetch("./api/model-geometry.json"',
        'fetch("/api/candidates"': 'fetch("./api/candidates.json"',
        'fetch("/api/mesh"': 'fetch("./api/mesh.json"',
        'fetch("/api/geometry-artifacts"': 'fetch("./api/geometry-artifacts.json"',
        'fetch("/api/assembly"': 'fetch("./api/assembly.json"',
        'fetch("/api/evidence-index"': 'fetch("./api/evidence-index.json"',
        'fetch("/api/axial-3d?score="+encodeURIComponent(score)+(forceRetry?"&retry=1":"")':
            'fetch("./api/axial-3d-"+encodeURIComponent(score)+".json"',
        '"/research_snapshot.json"': '"./research_snapshot.json"',
        'href="/"': 'href="./"',
        'href="/#': 'href="./#',
    }
    for name in static_files:
        file = SITE / name
        if not file.is_file():
            continue
        text = file.read_text(encoding="utf-8")
        for old, new in replacements.items():
            text = text.replace(old, new)
        for resource in static_files:
            text = text.replace(f'"/{resource}"', f'"./{resource}"')
            text = text.replace(f"'/{resource}'", f"'./{resource}'")
        text = text.replace('"/assets/', '"./assets/')
        text = text.replace("'/assets/", "'./assets/")
        text = text.replace('"/core_geometry_3d.js"', '"./core_geometry_3d.js"')
        file.write_text(text, encoding="utf-8")


def main() -> None:
    if not (WEB_ROOT / "index.html").is_file():
        raise FileNotFoundError("web/index.html is missing.")
    if SITE.exists():
        shutil.rmtree(SITE)
    shutil.copytree(WEB_ROOT, SITE, ignore=shutil.ignore_patterns("__pycache__", ".DS_Store"))
    (SITE / ".nojekyll").write_text("", encoding="utf-8")
    server = load_server_module()
    make_api_snapshot(server)
    rewrite_for_pages()

    # Fail the build if the published HTML still contains API/root-asset requests
    # that would silently target the host root instead of the project Pages path.
    html = (SITE / "index.html").read_text(encoding="utf-8")
    required = ["./styles.css", "./app.js", "./research_snapshot.json"]
    for value in required:
        if value not in html:
            raise ValueError(f"Published index.html is missing required relative reference: {value}")
    js = (SITE / "app.js").read_text(encoding="utf-8")
    for unresolved in ['fetch("/api/', 'fetch("/research_snapshot.json"', 'import("/core_geometry_3d.js")']:
        if unresolved in js:
            raise ValueError(f"Published app.js still contains unsupported server-root request: {unresolved}")
    print(f"Built static CB-PFR Pages site at {SITE} with {len(list(API_DIR.glob('*.json')))} recorded API snapshots.")


if __name__ == "__main__":
    main()
