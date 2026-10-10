#!/usr/bin/env python3
"""Inventory OpenMC run artifacts without modifying or executing simulations."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

PATTERNS = (
    "statepoint*.h5", "summary.h5", "openmc.log", "openmc.out",
    "settings.xml", "tallies.xml", "geometry.xml", "materials.xml",
    "plots.xml", "run_manifest.json", "result_summary.json",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.expanduser().resolve()
    if not root.is_dir():
        raise SystemExit(f"Run directory not found: {root}")

    paths = set()
    for pattern in PATTERNS:
        paths.update(root.rglob(pattern))
    entries = []
    for path in sorted(paths):
        try:
            entries.append({
                "relative_path": str(path.relative_to(root)),
                "size_bytes": path.stat().st_size,
                "sha256": sha256(path),
                "artifact_type": path.name.split(".")[0],
            })
        except OSError as exc:
            entries.append({
                "relative_path": str(path),
                "error": f"{type(exc).__name__}: {exc}",
            })

    output = {
        "root": str(root),
        "artifact_count": len(entries),
        "artifacts": entries,
        "limitations": [
            "Presence of a statepoint/log does not prove which candidate it belongs to.",
            "Candidate identity requires a matching configuration/manifest and input hashes.",
            "This inventory does not assert simulation success or physical validity."
        ],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(f"Inventoried {len(entries)} artifacts; wrote {args.out}")


if __name__ == "__main__":
    main()
