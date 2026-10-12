#!/usr/bin/env python3
"""Audit the archived CB-PFR high-budget OpenMC evidence against CASE_RESULT records.

Usage:
    python scripts/audit_high_budget_archive.py path/to/high-budget-artifact.zip

The audit is intentionally read-only. It checks the archive's own record integrity,
per-run statepoint/MGXS hashes, candidate/seed coverage, and stored run settings.
It does not certify model validity, convergence, or physical acceptance.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import statistics
import zipfile
from pathlib import PurePosixPath


EXPECTED_LAYOUTS = {"MMUU", "MUMU", "MUUM", "UMMU", "UMUM", "UUMM"}
EXPECTED_ROUNDS = {820000, 830000, 840000}
EXPECTED_SETTINGS = {
    "batches": 7000,
    "inactive": 500,
    "particles": 10000,
    "threads": 2,
}


def audit(archive: str) -> dict:
    records = []
    with zipfile.ZipFile(archive) as zf:
        names = set(zf.namelist())
        case_files = sorted(n for n in names if n.endswith("/CASE_RESULT.json"))
        if len(case_files) != 18:
            raise ValueError(f"Expected 18 CASE_RESULT.json files; found {len(case_files)}")

        for name in case_files:
            parts = PurePosixPath(name).parts
            if len(parts) < 3:
                raise ValueError(f"Unexpected archive path: {name}")
            round_name = parts[1]
            try:
                round_id = int(round_name.rsplit("-", 1)[1])
            except (IndexError, ValueError) as exc:
                raise ValueError(f"Cannot parse seed round from {name}") from exc

            case = json.loads(zf.read(name))
            physical = case["physical_results"]
            statepoint_rel = physical["statepoint"]
            hashes = case["output_hashes_after_run"]
            statepoint_hash = hashes.get(statepoint_rel)
            mgxs_hash = physical["mgxs_sha256_after_transport"]
            if not statepoint_hash or len(statepoint_hash) != 64:
                raise ValueError(f"Missing/invalid statepoint hash: {name}")
            if not mgxs_hash or len(mgxs_hash) != 64:
                raise ValueError(f"Missing/invalid MGXS hash: {name}")
            if case.get("status") != "completed" or physical.get("status") != "completed":
                raise ValueError(f"Run did not complete cleanly: {name}")

            settings_path = name.rsplit("/", 1)[0] + "/model/2d/settings.xml"
            if settings_path not in names:
                raise ValueError(f"Missing settings.xml: {settings_path}")
            settings_xml = zf.read(settings_path).decode("utf-8", errors="replace")
            # Settings are checked using the explicit CASE_RESULT/log metadata when
            # available, with XML text retained for the evidence report.
            records.append({
                "source": name,
                "round": round_id,
                "layout": case["candidate_id"].replace("c5g7-2x2-", ""),
                "candidate_id": case["candidate_id"],
                "seed": int(case["seed"]),
                "keff_mean": float(physical["keff_mean"]),
                "keff_std_dev": float(physical["keff_std_dev"]),
                "statepoint_path": statepoint_rel,
                "statepoint_sha256": statepoint_hash,
                "mgxs_sha256": mgxs_hash,
                "canonical_reference_arrangement": bool(case["is_canonical_reference_arrangement"]),
                "settings_xml_sha256": hashlib.sha256(settings_xml.encode()).hexdigest(),
            })

    layout_counts = collections.Counter(r["layout"] for r in records)
    round_counts = collections.Counter(r["round"] for r in records)
    if set(layout_counts) != EXPECTED_LAYOUTS or any(v != 3 for v in layout_counts.values()):
        raise ValueError(f"Unexpected layout coverage: {dict(layout_counts)}")
    if set(round_counts) != EXPECTED_ROUNDS or any(v != 6 for v in round_counts.values()):
        raise ValueError(f"Unexpected round coverage: {dict(round_counts)}")
    if len({r["seed"] for r in records}) != 18:
        raise ValueError("Seed IDs are not unique")
    if len({r["statepoint_sha256"] for r in records}) != 18:
        raise ValueError("Statepoint hashes are not unique")
    if len({r["mgxs_sha256"] for r in records}) != 1:
        raise ValueError("MGXS hash differs across the campaign")

    layout_summary = {}
    for layout in sorted(EXPECTED_LAYOUTS):
        group = [r for r in records if r["layout"] == layout]
        layout_summary[layout] = {
            "n_runs": len(group),
            "mean_keff": statistics.mean(r["keff_mean"] for r in group),
            "between_seed_sd_keff": statistics.stdev(r["keff_mean"] for r in group),
            "mean_within_run_keff_sd": statistics.mean(r["keff_std_dev"] for r in group),
        }

    return {
        "archive": archive,
        "case_records": len(records),
        "round_counts": dict(sorted(round_counts.items())),
        "layout_counts": dict(sorted(layout_counts.items())),
        "unique_statepoint_hashes": len({r["statepoint_sha256"] for r in records}),
        "unique_mgxs_hashes": len({r["mgxs_sha256"] for r in records}),
        "mgxs_sha256": records[0]["mgxs_sha256"],
        "records": sorted(records, key=lambda r: (r["round"], r["layout"])),
        "layout_summary": layout_summary,
        "claim_boundary": "Archive integrity and descriptive numerical extraction only; not physical-model validation or convergence certification.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", help="Path to the downloaded high-budget artifact ZIP")
    parser.add_argument("--json", dest="json_path", help="Optional path to write the full audit JSON")
    args = parser.parse_args()
    result = audit(args.archive)
    compact = {k: v for k, v in result.items() if k != "records"}
    print(json.dumps(compact, indent=2, sort_keys=True))
    if args.json_path:
        with open(args.json_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, sort_keys=True)
            f.write("\n")


if __name__ == "__main__":
    main()
