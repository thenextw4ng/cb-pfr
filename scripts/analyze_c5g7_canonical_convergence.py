#!/usr/bin/env python3
"""Aggregate repeated high-budget canonical C5G7 runs against provisional project screens."""
from __future__ import annotations

import argparse
import json
import math
import statistics
from pathlib import Path

C5G7_GROUP_BOUNDARIES = (1.0e-5, 0.0635, 10.0, 100.0, 1000.0, 500000.0, 1000000.0, 20000000.0)
REFERENCE_KEFF = 1.18655
REFERENCE_SD = 0.000095
HISTORICAL_PRODUCTION_BASELINE_KEFF = 1.186394144702191
HISTORICAL_PRODUCTION_BASELINE_SD = 5.6113408647969484e-05


def evaluate_runs(rows: list[dict], *, min_replicates: int = 3,
                  max_delta_pcm: float = 100.0, max_run_sd_pcm: float = 10.0,
                  max_z: float = 2.0) -> dict:
    if len(rows) < min_replicates:
        raise ValueError(f"need at least {min_replicates} canonical runs, got {len(rows)}")
    seeds = [int(r["seed"]) for r in rows]
    hashes = [r["statepoint_sha256"] for r in rows]
    mgxs_hashes = {r["mgxs_sha256"] for r in rows}
    settings = {(int(r["batches"]), int(r["inactive"]), int(r["particles_per_batch"]), int(r["threads"])) for r in rows}
    canonical_only = all(r["candidate_id"] == "c5g7-2x2-UMMU" and r["layout_signature"] == "UMMU" for r in rows)
    audit_pass = all(r["raw_hdf5_audit"] == "PASS" for r in rows)
    single_mgxs_hash = len(mgxs_hashes) == 1
    standard_group_structure = all(
        r.get("mgxs_group_structure_audit") == "PASS"
        and tuple(r.get("mgxs_energy_group_boundaries") or ()) == C5G7_GROUP_BOUNDARIES
        for r in rows
    )
    global_checks = {
        "canonical_candidate_only": canonical_only,
        "unique_seeds": len(seeds) == len(set(seeds)),
        "unique_statepoint_hashes": len(hashes) == len(set(hashes)),
        "common_compute_settings": len(settings) == 1,
        "raw_hdf5_audits_pass": audit_pass,
        "single_mgxs_hash_across_runs": single_mgxs_hash,
        "standard_c5g7_energy_group_structure": standard_group_structure,
    }
    means = [float(r["keff_mean"]) for r in rows]
    sds = [float(r["keff_std_dev"]) for r in rows]
    if any(not math.isfinite(v) for v in means + sds) or any(v <= 0 for v in sds):
        raise ValueError("keff means/standard deviations must be finite and SD positive")
    mean_keff = statistics.mean(means)
    between_sd = statistics.stdev(means) if len(means) > 1 else 0.0
    pooled_within_sd = math.sqrt(sum(v*v for v in sds) / len(sds))
    mean_se = between_sd / math.sqrt(len(means))
    combined_se = math.sqrt(REFERENCE_SD**2 + mean_se**2)
    delta_pcm = (mean_keff - REFERENCE_KEFF) * 1e5
    z_score = (mean_keff - REFERENCE_KEFF) / combined_se
    max_run_sd_pcm_observed = max(sds) * 1e5
    numerical_screen_pass = (
        all(global_checks.values())
        and abs(delta_pcm) <= max_delta_pcm
        and abs(z_score) <= max_z
        and max_run_sd_pcm_observed <= max_run_sd_pcm
    )
    if not all(global_checks.values()):
        status = "FAIL_DATA_INTEGRITY_OR_MODEL_IDENTITY"
    elif numerical_screen_pass:
        status = "NUMERICAL_SCREEN_PASS_FULL_BENCHMARK_STILL_BLOCKED"
    else:
        status = "FAIL_OR_INCOMPLETE_NUMERICAL_SCREEN"
    return {
        "schema_version": "1.0",
        "protocol_id": "CBPFR-C5G7-validation-gates-2026-10-11",
        "status": status,
        "is_official_benchmark_acceptance": False,
        "candidate_id": "c5g7-2x2-UMMU",
        "layout_signature": "UMMU",
        "run_count": len(rows),
        "seeds": seeds,
        "statepoint_sha256": hashes,
        "settings_profile": next(iter(settings)) if len(settings) == 1 else None,
        "global_checks": global_checks,
        "reference": {"keff": REFERENCE_KEFF, "standard_uncertainty": REFERENCE_SD},
        "historical_production_baseline": {
            "keff": HISTORICAL_PRODUCTION_BASELINE_KEFF,
            "reported_sd": HISTORICAL_PRODUCTION_BASELINE_SD,
            "comparability": "NOT_COMPARABLE",
            "reason": "Historical production MGXS used nonstandard log-spaced energy boundaries."
        },
        "limits": {"absolute_reference_delta_pcm_max": max_delta_pcm,
                   "combined_uncertainty_z_max": max_z,
                   "per_run_reported_sd_pcm_max": max_run_sd_pcm,
                   "minimum_replicates": min_replicates},
        "metrics": {
            "mean_keff": mean_keff,
            "between_run_sample_sd": between_sd,
            "pooled_within_run_reported_sd": pooled_within_sd,
            "mean_combined_standard_uncertainty": combined_se,
            "reference_delta_pcm": delta_pcm,
            "combined_uncertainty_z": z_score,
            "max_single_run_sd_pcm": max_run_sd_pcm_observed,
            "numerical_screen_pass": numerical_screen_pass,
        },
        "runs": rows,
        "model_identity_reviewed_against_primary_specification": False,
        "spatial_reference_tally_reviewed": False,
        "interpretation": (
            "This is a project-level numerical screen, not official benchmark acceptance. "
            "Even if the scalar gates pass, primary-specification review and a benchmark-compatible "
            "spatial tally comparison remain mandatory. A k-effective match alone is not validation."
        ),
    }


def load_runs(root: Path) -> list[dict]:
    rows = []
    for round_dir in sorted(root.glob("seed_*")):
        summary_path = round_dir / "STUDY_SUMMARY.json"
        audit_path = round_dir / "analysis" / "raw_hdf5_audit.json"
        if not summary_path.is_file() or not audit_path.is_file():
            raise ValueError(f"{round_dir.name}: missing STUDY_SUMMARY.json or raw HDF5 audit")
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        audit = json.loads(audit_path.read_text(encoding="utf-8"))
        if summary.get("status") != "all_runs_completed_needs_independent_validation":
            raise ValueError(f"{round_dir.name}: run study status is {summary.get('status')}")
        if audit.get("status") != "PASS" or audit.get("candidate_count") != 1:
            raise ValueError(f"{round_dir.name}: raw HDF5 audit did not pass for one candidate")
        if len(summary.get("cases", [])) != 1:
            raise ValueError(f"{round_dir.name}: expected exactly one selected candidate")
        case = summary["cases"][0]
        physical = case.get("physical_results") or {}
        audit_case = audit["candidates"][0]
        rows.append({
            "round": round_dir.name,
            "candidate_id": case.get("candidate_id"),
            "layout_signature": "".join("M" if case["layout"][p] == "MOX" else "U" for p in ("p00", "p01", "p10", "p11")),
            "seed": int(case["seed"]),
            "batches": int(summary["settings"]["batches"]),
            "inactive": int(summary["settings"]["inactive"]),
            "particles_per_batch": int(summary["settings"]["particles"]),
            "threads": int(summary["settings"]["threads"]),
            "keff_mean": float(physical["keff_mean"]),
            "keff_std_dev": float(physical["keff_std_dev"]),
            "statepoint_sha256": audit_case["statepoint_sha256"],
            "settings_sha256": audit_case["settings_sha256"],
            "mgxs_sha256": audit_case["mgxs_sha256"],
            "mgxs_energy_group_boundaries": physical.get("mgxs_energy_group_boundaries"),
            "mgxs_group_structure_audit": physical.get("mgxs_group_structure_audit"),
            "raw_hdf5_audit": audit["status"],
        })
    if not rows:
        raise ValueError(f"no seed_* run directories found under {root}")
    return rows


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--rounds-root", required=True, type=Path)
    p.add_argument("--out-json", required=True, type=Path)
    p.add_argument("--out-md", required=True, type=Path)
    p.add_argument("--max-run-sd-pcm", type=float, default=10.0)
    a = p.parse_args()
    if a.out_json.exists() or a.out_md.exists():
        p.error("refusing to overwrite existing output files")
    try:
        rows = load_runs(a.rounds_root)
        report = evaluate_runs(rows, max_run_sd_pcm=a.max_run_sd_pcm)
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        p.error(str(exc))
    a.out_json.parent.mkdir(parents=True, exist_ok=True)
    a.out_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    m = report["metrics"]
    markdown = f"""# Canonical C5G7 repeated-run numerical screen

Status: **{report['status']}**

Runs: {report['run_count']}; unique seeds: {len(set(report['seeds']))}; standard C5G7 energy-group structure: {report['global_checks']['standard_c5g7_energy_group_structure']}.

| Metric | Value |
|---|---:|
| Mean k-effective | {m['mean_keff']:.8f} |
| Between-run sample SD | {m['between_run_sample_sd']:.8f} |
| Pooled within-run reported SD | {m['pooled_within_run_reported_sd']:.8f} |
| Difference from reference | {m['reference_delta_pcm']:.2f} pcm |
| Combined-uncertainty z | {m['combined_uncertainty_z']:.3f} |
| Maximum individual-run SD | {m['max_single_run_sd_pcm']:.2f} pcm |

The archived production scalar is not used as a comparison target because its historical MGXS group boundaries were nonstandard. This is a provisional project numerical screen, not official benchmark acceptance. Primary-specification review and benchmark-compatible spatial tallies remain mandatory even if the scalar screen passes.
"""
    a.out_md.write_text(markdown, encoding="utf-8")
    print(json.dumps({"status": report["status"], "run_count": report["run_count"],
                      "metrics": report["metrics"], "out_json": str(a.out_json), "out_md": str(a.out_md)}, indent=2))
    return 0 if report["status"] in ("NUMERICAL_SCREEN_PASS_FULL_BENCHMARK_STILL_BLOCKED", "FAIL_OR_INCOMPLETE_NUMERICAL_SCREEN") else 2


if __name__ == "__main__":
    raise SystemExit(main())
