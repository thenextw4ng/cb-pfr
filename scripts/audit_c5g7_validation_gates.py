#!/usr/bin/env python3
"""Audit repeated C5G7 run CSVs against project screening gates.

This tool separates descriptive repeatability from benchmark acceptance. By
default, benchmark acceptance remains blocked because model identity and
benchmark-compatible spatial reference data require independent review.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path

REQUIRED = {
    "candidate_id", "layout_signature", "seed", "batches", "inactive",
    "particles_per_batch", "keff_mean", "keff_std_dev", "statepoint_sha256",
    "settings_sha256", "mgxs_sha256", "raw_hdf5_audit",
}


def load_rows(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        missing = REQUIRED - set(reader.fieldnames or ())
        if missing:
            raise ValueError(f"input CSV missing required columns: {sorted(missing)}")
        rows = list(reader)
    if not rows:
        raise ValueError("input CSV contains no run rows")
    for index, row in enumerate(rows, start=2):
        try:
            row["_seed"] = int(row["seed"])
            row["_batches"] = int(row["batches"])
            row["_inactive"] = int(row["inactive"])
            row["_particles"] = int(row["particles_per_batch"])
            row["_keff"] = float(row["keff_mean"])
            row["_sd"] = float(row["keff_std_dev"])
        except (TypeError, ValueError) as exc:
            raise ValueError(f"invalid numeric field on CSV line {index}") from exc
        if row["_batches"] <= row["_inactive"] or row["_inactive"] < 0 or row["_particles"] < 1:
            raise ValueError(f"invalid run settings on CSV line {index}")
        if not math.isfinite(row["_keff"]) or not math.isfinite(row["_sd"]) or row["_sd"] <= 0:
            raise ValueError(f"invalid keff/uncertainty on CSV line {index}")
    return rows


def audit_rows(rows: list[dict], reference_keff: float = 1.18655,
               reference_sd: float = 0.000095, min_replicates: int = 3,
               max_delta_pcm: float = 100.0, max_run_sd_pcm: float = 10.0,
               max_z: float = 2.0, model_identity_reviewed: bool = False,
               tally_reference_reviewed: bool = False) -> dict:
    if min_replicates < 2:
        raise ValueError("min_replicates must be at least 2")
    if reference_sd <= 0 or max_delta_pcm <= 0 or max_run_sd_pcm <= 0 or max_z <= 0:
        raise ValueError("reference uncertainty and screening limits must be positive")
    candidates = defaultdict(list)
    for row in rows:
        candidates[row["candidate_id"]].append(row)
    settings = {(r["_batches"], r["_inactive"], r["_particles"]) for r in rows}
    threads_not_in_schema = True
    seeds = [r["_seed"] for r in rows]
    statepoint_hashes = [r["statepoint_sha256"] for r in rows]
    mgxs_hashes = {r["mgxs_sha256"] for r in rows}
    raw_audits_pass = all(r["raw_hdf5_audit"] == "PASS" for r in rows)
    global_checks = {
        "common_compute_settings": len(settings) == 1,
        "unique_seeds": len(seeds) == len(set(seeds)),
        "unique_statepoint_hashes": len(statepoint_hashes) == len(set(statepoint_hashes)),
        "single_mgxs_hash": len(mgxs_hashes) == 1,
        "all_raw_hdf5_audits_pass": raw_audits_pass,
        "thread_count_in_csv": not threads_not_in_schema,
    }
    per_candidate = []
    for cid, group in sorted(candidates.items()):
        group_seeds = [r["_seed"] for r in group]
        means = [r["_keff"] for r in group]
        within = [r["_sd"] for r in group]
        between_sd = statistics.stdev(means) if len(means) > 1 else None
        pooled_within = math.sqrt(sum(s*s for s in within) / len(within))
        mean_keff = statistics.mean(means)
        # The repeated-run sample SD captures run-to-run spread; do not add the
        # within-run SD again to this standard error (that would double-count).
        mean_se = (between_sd / math.sqrt(len(means))) if between_sd is not None else pooled_within
        combined_se = math.sqrt(reference_sd**2 + mean_se**2)
        z_score = (mean_keff - reference_keff) / combined_se
        delta_pcm = (mean_keff - reference_keff) * 1e5
        run_sd_max_pcm = max(within) * 1e5
        complete = (
            len(group) >= min_replicates
            and len(group_seeds) == len(set(group_seeds))
            and all(r["raw_hdf5_audit"] == "PASS" for r in group)
            and len({r["statepoint_sha256"] for r in group}) == len(group)
        )
        scalar_screen_pass = (
            complete
            and abs(delta_pcm) <= max_delta_pcm
            and abs(z_score) <= max_z
            and run_sd_max_pcm <= max_run_sd_pcm
        )
        per_candidate.append({
            "candidate_id": cid,
            "layout_signature": group[0]["layout_signature"],
            "replicate_count": len(group),
            "unique_seed_count": len(set(group_seeds)),
            "mean_keff": mean_keff,
            "between_run_sample_sd": between_sd,
            "pooled_within_run_reported_sd": pooled_within,
            "max_single_run_sd_pcm": run_sd_max_pcm,
            "reference_delta_pcm": delta_pcm,
            "combined_uncertainty_z": z_score,
            "repeatability_data_complete": complete,
            "keff_scalar_screen_pass": scalar_screen_pass,
            "ranking_is_descriptive_only": True,
        })
    canonical = next((c for c in per_candidate if c["layout_signature"] == "UMMU"), None)
    global_pass = all(global_checks[k] for k in (
        "common_compute_settings", "unique_seeds", "unique_statepoint_hashes",
        "single_mgxs_hash", "all_raw_hdf5_audits_pass"
    ))
    if not global_pass:
        status = "FAIL_DATA_INTEGRITY_OR_COMMON_SETTINGS"
    elif canonical is None or not canonical["keff_scalar_screen_pass"]:
        status = "FAIL_OR_INCOMPLETE_CANONICAL_KEFF_SCREEN"
    elif not model_identity_reviewed:
        status = "BLOCKED_MODEL_IDENTITY_REVIEW"
    elif not tally_reference_reviewed:
        status = "BLOCKED_SPATIAL_TALLY_REFERENCE_REVIEW"
    elif not all(c["repeatability_data_complete"] for c in per_candidate):
        status = "INCOMPLETE_CANDIDATE_REPEATABILITY"
    else:
        status = "PROJECT_SCREEN_PASSED_NOT_OFFICIAL_BENCHMARK_CERTIFICATION"
    return {
        "schema_version": "1.0",
        "protocol_id": "CBPFR-C5G7-validation-gates-2026-10-11",
        "status": status,
        "is_official_benchmark_acceptance": False,
        "reference": {"keff": reference_keff, "standard_uncertainty": reference_sd},
        "limits": {"minimum_replicates": min_replicates,
                   "absolute_delta_pcm_max": max_delta_pcm,
                   "per_run_reported_sd_pcm_max": max_run_sd_pcm,
                   "combined_uncertainty_z_max": max_z},
        "run_count": len(rows),
        "candidate_count": len(per_candidate),
        "global_checks": global_checks,
        "model_identity_reviewed": model_identity_reviewed,
        "tally_reference_reviewed": tally_reference_reviewed,
        "candidates": per_candidate,
        "interpretation": (
            "This is a project-level screening report. It cannot establish benchmark "
            "validity until exact model identity and reference-compatible spatial tallies "
            "are independently reviewed. A passing scalar screen is not a safety claim."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs-csv", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--reference-keff", type=float, default=1.18655)
    parser.add_argument("--reference-sd", type=float, default=0.000095)
    parser.add_argument("--min-replicates", type=int, default=3)
    parser.add_argument("--max-delta-pcm", type=float, default=100.0)
    parser.add_argument("--max-run-sd-pcm", type=float, default=10.0)
    parser.add_argument("--max-z", type=float, default=2.0)
    parser.add_argument("--model-identity-reviewed", action="store_true",
                        help="only after independent review of exact model/material/settings provenance")
    parser.add_argument("--tally-reference-reviewed", action="store_true",
                        help="only after compatible spatial reference data and normalization are reviewed")
    args = parser.parse_args()
    if args.out.exists():
        parser.error(f"refusing to overwrite existing output: {args.out}")
    try:
        rows = load_rows(args.runs_csv)
        report = audit_rows(
            rows, args.reference_keff, args.reference_sd, args.min_replicates,
            args.max_delta_pcm, args.max_run_sd_pcm, args.max_z,
            args.model_identity_reviewed, args.tally_reference_reviewed,
        )
    except (OSError, ValueError, csv.Error) as exc:
        parser.error(str(exc))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "run_count": report["run_count"],
                      "candidate_count": report["candidate_count"],
                      "output": str(args.out)}, indent=2))
    return 0 if report["status"] not in ("FAIL_DATA_INTEGRITY_OR_COMMON_SETTINGS",) else 2


if __name__ == "__main__":
    raise SystemExit(main())
