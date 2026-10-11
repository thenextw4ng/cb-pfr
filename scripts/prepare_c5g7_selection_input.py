#!/usr/bin/env python3
"""Validate and enrich archived corrected-group C5G7 smoke rows for a CB-PFR gate.

The archived fission-objective CSV omits compute settings and explicit group
boundaries. This adapter restores only the settings declared by the archived
smoke protocol (100 batches, 10 inactive, 1000 particles, one thread), and fails
closed unless the dataset is exactly the expected 18-run/6-layout/3-round study.
It does not upgrade smoke data to benchmark-grade evidence.
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path

EXPECTED = {"MMUU", "MUMU", "MUUM", "UMMU", "UMUM", "UUMM"}
GROUP_EDGES = "1e-05;0.0635;10.0;100.0;1000.0;500000.0;1000000.0;20000000.0"
SETTINGS = {"batches": 100, "inactive": 10, "particles_per_batch": 1000, "threads": 1}
REQUIRED = {
    "round", "candidate_id", "layout_signature", "seed", "keff_mean",
    "keff_std_dev", "fission_rate_peaking_factor", "statepoint_sha256",
    "mgxs_sha256", "group_structure_audit",
}


def prepare(source: Path, output: Path) -> dict:
    with source.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        missing = REQUIRED - set(reader.fieldnames or ())
        if missing:
            raise ValueError(f"input CSV missing required columns: {sorted(missing)}")
        rows = list(reader)
    if len(rows) != 18:
        raise ValueError(f"expected exactly 18 archived runs, found {len(rows)}")
    if output.exists():
        raise ValueError(f"refusing to overwrite existing output: {output}")

    round_names = {r["round"] for r in rows}
    if len(round_names) != 3:
        raise ValueError(f"expected 3 independent seed rounds, found {len(round_names)}")
    counts = Counter(r["layout_signature"] for r in rows)
    if set(counts) != EXPECTED or any(counts[sig] != 3 for sig in EXPECTED):
        raise ValueError(f"expected all six layouts with 3 runs each, found {dict(counts)}")
    ids = [r["candidate_id"] for r in rows]
    if any(r["candidate_id"] != f"c5g7-2x2-{r['layout_signature']}" for r in rows):
        raise ValueError("candidate ID/layout signature mismatch")
    seeds = [int(r["seed"]) for r in rows]
    if len(set(seeds)) != 18:
        raise ValueError("seed values must be unique across all 18 runs")
    statepoint_hashes = [r["statepoint_sha256"] for r in rows]
    if any(not value for value in statepoint_hashes) or len(set(statepoint_hashes)) != 18:
        raise ValueError("statepoint hashes must be present and unique")
    mgxs_hashes = {r["mgxs_sha256"] for r in rows}
    if len(mgxs_hashes) != 1:
        raise ValueError("all rows must use one shared MGXS hash")
    if any(r["group_structure_audit"] != "PASS" for r in rows):
        raise ValueError("not all archived rows pass the corrected group-structure audit")

    output.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "round", "candidate_id", "layout_signature", "seed",
        "keff_mean", "keff_std_dev", "fission_rate_peaking_factor",
        "statepoint_sha256", "mgxs_sha256", "group_structure_audit",
        "mgxs_energy_group_boundaries_eV", "batches", "inactive",
        "particles_per_batch", "threads", "uncertainty_note",
    ]
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            enriched = {key: row.get(key, "") for key in fields}
            enriched.update(SETTINGS)
            enriched["mgxs_energy_group_boundaries_eV"] = GROUP_EDGES
            enriched["uncertainty_note"] = (
                "exploratory smoke only; between-seed spread is not a calibrated confidence interval"
            )
            writer.writerow(enriched)

    return {
        "status": "INPUT_INTEGRITY_PASS_SMOKE_EVIDENCE_ONLY",
        "source_csv": str(source),
        "output_csv": str(output),
        "run_count": len(rows),
        "round_count": len(round_names),
        "layout_count": len(counts),
        "runs_per_layout": 3,
        "settings": SETTINGS,
        "group_boundaries_eV": GROUP_EDGES,
        "unique_statepoint_hashes": True,
        "single_mgxs_hash": next(iter(mgxs_hashes)),
        "physical_validation_claim": "NOT_ESTABLISHED",
        "limits": [
            "100 batches / 10 inactive / 1000 particles is exploratory smoke budget.",
            "No design-specific acceptable keff band has been established.",
            "The fission-peaking uncertainty heuristic is not a calibrated confidence interval.",
            "This adapter does not rerun OpenMC or certify a physically optimal layout.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--audit-out", type=Path, required=True)
    args = parser.parse_args()
    try:
        report = prepare(args.input, args.output)
    except (OSError, ValueError, KeyError) as exc:
        parser.error(str(exc))
    args.audit_out.parent.mkdir(parents=True, exist_ok=True)
    args.audit_out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "run_count": report["run_count"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
