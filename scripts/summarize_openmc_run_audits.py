#!/usr/bin/env python3
"""Create a run-level table from one or more OpenMC statepoint audit JSON files."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit-root", required=True, type=Path)
    parser.add_argument("--out-csv", required=True, type=Path)
    parser.add_argument("--out-json", required=True, type=Path)
    args = parser.parse_args()
    for output in (args.out_csv, args.out_json):
        if output.exists():
            parser.error(f"output already exists: {output}")
    if not args.audit_root.is_dir():
        parser.error(f"audit root does not exist: {args.audit_root}")

    rows = []
    for path in sorted(args.audit_root.rglob("statepoint_audit.json")):
        audit = json.loads(path.read_text(encoding="utf-8"))
        keff = audit.get("keff") or {}
        rows.append({
            "audit_file": str(path.relative_to(args.audit_root)),
            "statepoint_path": audit.get("statepoint_path"),
            "statepoint_read_success": audit.get("statepoint_read_success"),
            "openmc_version": audit.get("openmc_version"),
            "run_mode": audit.get("run_mode"),
            "n_batches": audit.get("n_batches"),
            "n_inactive": audit.get("n_inactive"),
            "n_particles": audit.get("n_particles"),
            "n_realizations": audit.get("n_realizations"),
            "keff_mean": keff.get("mean"),
            "keff_std_dev": keff.get("std_dev"),
            "tally_count": len(audit.get("tallies", [])),
            "candidate_id": None,
            "candidate_mapping_status": "unmatched; no verified candidate manifest in this audit record",
        })
    if not rows:
        parser.error(f"no statepoint_audit.json files found under {args.audit_root}")
    args.out_csv.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    with args.out_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    args.out_json.write_text(json.dumps({
        "schema_version": "1.0",
        "audit_count": len(rows),
        "statepoint_read_success_count": sum(bool(row["statepoint_read_success"]) for row in rows),
        "candidate_identity_verified_count": 0,
        "rows": rows,
        "limitations": [
            "A statepoint is not associated with an optimization candidate without a verified manifest/configuration hash.",
            "Differences between runs are not interpreted as optimizer repeatability unless settings and candidate identities are matched.",
        ],
    }, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "audit_count": len(rows),
        "statepoint_read_success_count": sum(bool(row["statepoint_read_success"]) for row in rows),
        "out_csv": str(args.out_csv),
        "out_json": str(args.out_json),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
