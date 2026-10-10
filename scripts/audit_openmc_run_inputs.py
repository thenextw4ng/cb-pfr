#!/usr/bin/env python3
"""Inventory OpenMC settings/log provenance without interpreting candidate identity."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    if not args.root.is_dir():
        parser.error(f"input root does not exist: {args.root}")
    if args.out.exists():
        parser.error(f"output already exists: {args.out}")

    settings_rows = []
    for path in sorted(args.root.rglob("settings.xml")):
        row = {
            "relative_path": str(path.relative_to(args.root)),
            "size_bytes": path.stat().st_size,
            "sha256": sha256(path),
            "parsed": False,
        }
        try:
            root = ET.parse(path).getroot()
            for tag in ("run_mode", "energy_mode", "batches", "inactive", "particles", "seed", "generations_per_batch", "output"):
                node = root.find(tag)
                if node is not None:
                    row[tag] = (node.text or "").strip()
            row["parsed"] = True
        except (ET.ParseError, OSError) as exc:
            row["parse_error"] = f"{type(exc).__name__}: {exc}"
        settings_rows.append(row)

    log_rows = []
    for path in sorted(args.root.rglob("openmc.log")):
        log_rows.append({
            "relative_path": str(path.relative_to(args.root)),
            "size_bytes": path.stat().st_size,
            "sha256": sha256(path),
        })

    settings_hash_groups = {}
    for row in settings_rows:
        settings_hash_groups.setdefault(row["sha256"], []).append(row["relative_path"])
    return_data = {
        "schema_version": "1.0",
        "root": str(args.root),
        "settings_file_count": len(settings_rows),
        "log_file_count": len(log_rows),
        "settings": settings_rows,
        "logs": log_rows,
        "identical_settings_hash_groups": [
            {"sha256": digest, "paths": paths}
            for digest, paths in settings_hash_groups.items() if len(paths) > 1
        ],
        "limitations": [
            "Matching settings files do not prove that statepoints belong to distinct candidates or independent random streams.",
            "Candidate identity still requires a configuration-to-run manifest and input hashes.",
        ],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(return_data, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "settings_file_count": len(settings_rows),
        "log_file_count": len(log_rows),
        "identical_settings_hash_groups": return_data["identical_settings_hash_groups"],
        "output": str(args.out),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
