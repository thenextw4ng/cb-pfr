#!/usr/bin/env python3
"""Audit archived CB-PFR high-budget OpenMC evidence against CASE_RESULT records.

Usage:
    python scripts/audit_high_budget_archive.py path/to/high-budget-artifact.zip

Read-only audit of run records, settings, provenance hashes, candidate/seed coverage,
and descriptive k-effective summaries. It does not certify physical-model validity,
convergence, or physical acceptance.
"""
from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import io
import json
import statistics
import xml.etree.ElementTree as ET
import zipfile
from pathlib import PurePosixPath

EXPECTED_LAYOUTS = {"MMUU", "MUMU", "MUUM", "UMMU", "UMUM", "UUMM"}
EXPECTED_ROUNDS = {820000, 830000, 840000}
EXPECTED_XML_SETTINGS = {"batches": 7000, "inactive": 500, "particles": 10000}


def audit(archive: str, bridge_csv: str | None = None) -> dict:
    records = []
    with zipfile.ZipFile(archive) as zf:
        names = set(zf.namelist())
        embedded_csv = "results/c5g7_six_layout_confirmation_2026-10-12/run_level_results.csv"
        if embedded_csv not in names:
            raise ValueError(f"Missing archive source-of-truth CSV: {embedded_csv}")
        archive_csv_rows = list(csv.DictReader(io.TextIOWrapper(zf.open(embedded_csv), encoding="utf-8")))
        if len(archive_csv_rows) != 18:
            raise ValueError(f"Expected 18 rows in embedded run-level CSV; found {len(archive_csv_rows)}")
        case_files = sorted(n for n in names if n.endswith("/CASE_RESULT.json"))
        if len(case_files) != 18:
            raise ValueError(f"Expected 18 CASE_RESULT.json files; found {len(case_files)}")

        for name in case_files:
            parts = PurePosixPath(name).parts
            if len(parts) < 3:
                raise ValueError(f"Unexpected archive path: {name}")
            try:
                round_id = int(parts[1].rsplit("-", 1)[1])
            except (IndexError, ValueError) as exc:
                raise ValueError(f"Cannot parse seed round from {name}") from exc

            case = json.loads(zf.read(name))
            physical = case["physical_results"]
            statepoint_rel = physical["statepoint"]
            statepoint_hash = case["output_hashes_after_run"].get(statepoint_rel)
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
            settings_bytes = zf.read(settings_path)
            root = ET.fromstring(settings_bytes)
            xml_settings = {}
            for key, expected in EXPECTED_XML_SETTINGS.items():
                node = root.find(key)
                if node is None or node.text is None or int(node.text.strip()) != expected:
                    raise ValueError(f"Unexpected/missing {key} in {settings_path}")
                xml_settings[key] = int(node.text.strip())
            seed_node = root.find("seed")
            if seed_node is None or int(seed_node.text.strip()) != int(case["seed"]):
                raise ValueError(f"Settings seed mismatch: {name}")

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
                "settings_xml_sha256": hashlib.sha256(settings_bytes).hexdigest(),
                **xml_settings,
            })

    csv_by_key = {(int(row["round"]), row["layout_signature"]): row for row in archive_csv_rows}
    record_by_key = {(r["round"], r["layout"]): r for r in records}
    if len(csv_by_key) != 18 or set(csv_by_key) != set(record_by_key):
        raise ValueError("Embedded run-level CSV does not cover the same 18 round/layout records")
    for key, record in record_by_key.items():
        row = csv_by_key[key]
        checks = {"candidate_id": record["candidate_id"], "seed": str(record["seed"]),
                  "statepoint_sha256": record["statepoint_sha256"], "mgxs_sha256": record["mgxs_sha256"],
                  "keff_mean": record["keff_mean"], "keff_std_dev": record["keff_std_dev"]}
        for field, expected in checks.items():
            equal = (abs(float(row[field]) - float(expected)) <= 1e-14
                     if field in {"keff_mean", "keff_std_dev"} else row[field] == str(expected))
            if not equal:
                raise ValueError(f"Embedded CSV mismatch at {key}, field {field}: {row[field]!r} != {expected!r}")

    bridge_comparison = {"requested": bridge_csv is not None, "status": "not_requested"}
    if bridge_csv is not None:
        with open(bridge_csv, newline="", encoding="utf-8-sig") as handle:
            bridge_rows = list(csv.DictReader(handle))
        bridge_by_key = {(int(row["round"]), row["layout_signature"]): row for row in bridge_rows}
        if len(bridge_by_key) != 18 or set(bridge_by_key) != set(csv_by_key):
            raise ValueError("Bridge CSV must contain exactly the same 18 unique round/layout records")
        fields = ("candidate_id", "seed", "keff_mean", "keff_std_dev",
                  "fission_rate_peaking_factor", "statepoint_sha256", "mgxs_sha256",
                  "batches", "inactive", "particles_per_batch", "threads")
        for key, source_row in csv_by_key.items():
            bridge_row = bridge_by_key[key]
            for field in fields:
                if field not in bridge_row or field not in source_row:
                    raise ValueError(f"Bridge/source CSV missing comparable field {field!r}")
                equal = (abs(float(bridge_row[field]) - float(source_row[field])) <= 1e-12
                         if field in {"keff_mean", "keff_std_dev", "fission_rate_peaking_factor"}
                         else str(bridge_row[field]) == str(source_row[field]))
                if not equal:
                    raise ValueError(f"Bridge CSV mismatch at {key}, field {field}: {bridge_row[field]!r} != {source_row[field]!r}")
        bridge_comparison = {"requested": True, "status": "PASS", "rows_compared": len(bridge_rows),
                             "fields_compared_per_row": list(fields)}

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
        "embedded_run_level_csv_check": "PASS",
        "bridge_csv_comparison": bridge_comparison,
        "claim_boundary": "Archive integrity and descriptive numerical extraction only; not physical-model validation or convergence certification.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", help="Path to the downloaded high-budget artifact ZIP")
    parser.add_argument("--json", dest="json_path", help="Optional path to write the full audit JSON")
    parser.add_argument("--bridge-csv", help="Optional repository bridge CSV to compare against the archived run-level CSV")
    args = parser.parse_args()
    result = audit(args.archive, bridge_csv=args.bridge_csv)
    print(json.dumps({k: v for k, v in result.items() if k != "records"}, indent=2, sort_keys=True))
    if args.json_path:
        with open(args.json_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, sort_keys=True)
            f.write("\n")


if __name__ == "__main__":
    main()
