#!/usr/bin/env python3
"""Reanalyze corrected C5G7 smoke artifacts for descriptive fission-peaking repeatability.

This tool consumes already-completed statepoints; it does not run transport.
It deliberately never declares a physical winner because a design-specific
k_eff acceptance band and benchmark-grade convergence have not been established.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
from pathlib import Path

C5G7_GROUP_BOUNDARIES = (1.0e-5, 0.0635, 10.0, 100.0, 1000.0, 500000.0, 1000000.0, 20000000.0)
POSITIONS = ("p00", "p01", "p10", "p11")


def sample_sd(values: list[float]) -> float | None:
    return statistics.stdev(values) if len(values) >= 2 else None


def analyze_study(study_root: Path) -> tuple[list[dict], list[dict], dict]:
    from analyze_c5g7_assembly_fission import analyze_statepoint

    run_rows = []
    rounds = sorted(p for p in study_root.iterdir() if p.is_dir() and p.name.startswith("round_"))
    if len(rounds) < 2:
        raise ValueError("need at least two independent round directories")
    for round_dir in rounds:
        summary_path = round_dir / "STUDY_SUMMARY.json"
        if not summary_path.is_file():
            raise ValueError(f"{round_dir.name}: missing STUDY_SUMMARY.json")
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        if summary.get("status") != "all_runs_completed_needs_independent_validation":
            raise ValueError(f"{round_dir.name}: study summary status is not completed")
        for case in summary.get("cases", []):
            candidate_id = case["candidate_id"]
            physical = case.get("physical_results", {})
            if case.get("status") != "completed" or physical.get("status") != "completed":
                raise ValueError(f"{round_dir.name}/{candidate_id}: run incomplete")
            if physical.get("mgxs_group_structure_audit") != "PASS":
                raise ValueError(f"{round_dir.name}/{candidate_id}: MGXS group-structure audit missing")
            edges = tuple(physical.get("mgxs_energy_group_boundaries") or ())
            if edges != C5G7_GROUP_BOUNDARIES:
                raise ValueError(f"{round_dir.name}/{candidate_id}: nonstandard energy-group boundaries {edges}")
            statepoint_rel = physical.get("statepoint")
            if not statepoint_rel:
                raise ValueError(f"{round_dir.name}/{candidate_id}: missing statepoint path")
            statepoint = round_dir / candidate_id / statepoint_rel
            signature = "".join("M" if case["layout"][position] == "MOX" else "U" for position in POSITIONS)
            result = analyze_statepoint(statepoint, candidate_id, signature)
            if result.get("layout_signature") != signature:
                raise ValueError(f"{round_dir.name}/{candidate_id}: tally layout signature mismatch")
            output_hashes = case.get("output_hashes_after_run", {})
            settings = summary.get("settings", {})
            required_settings = ("batches", "inactive", "particles", "threads")
            if any(key not in settings for key in required_settings):
                raise ValueError(f"{round_dir.name}: study settings lack a complete common compute profile")
            run_rows.append({
                "round": round_dir.name,
                "batches": int(settings["batches"]),
                "inactive": int(settings["inactive"]),
                "particles_per_batch": int(settings["particles"]),
                "threads": int(settings["threads"]),
                "candidate_id": candidate_id,
                "layout_signature": signature,
                "seed": physical.get("seed", case.get("seed")),
                "keff_mean": float(result["keff_mean"]),
                "keff_std_dev": float(result["keff_std_dev"]),
                "fission_rate_peaking_factor": float(result["fission_rate_peaking_factor"]),
                **{f"R_{position}": float(result["assembly_integrated_fission_rate"][position]) for position in POSITIONS},
                "statepoint_sha256": output_hashes.get("model/2d/statepoint.100.h5"),
                "mgxs_sha256": output_hashes.get("model/2d/mgxs.h5"),
                "group_structure_audit": physical.get("mgxs_group_structure_audit"),
                "mgxs_energy_group_boundaries_eV": ";".join(str(v) for v in edges),
                "uncertainty_note": result["uncertainty_status"],
            })
    by_candidate: dict[str, list[dict]] = {}
    for row in run_rows:
        by_candidate.setdefault(row["candidate_id"], []).append(row)
    if len(by_candidate) != 6:
        raise ValueError(f"expected six candidate layouts, found {len(by_candidate)}")
    summaries = []
    for candidate_id, rows in sorted(by_candidate.items()):
        if len(rows) != len(rounds):
            raise ValueError(f"{candidate_id}: expected one run in each of {len(rounds)} rounds, found {len(rows)}")
        f_values = [r["fission_rate_peaking_factor"] for r in rows]
        k_values = [r["keff_mean"] for r in rows]
        within = [r["keff_std_dev"] for r in rows]
        mean_f = statistics.mean(f_values)
        sd_f = sample_sd(f_values)
        summaries.append({
            "candidate_id": candidate_id,
            "layout_signature": rows[0]["layout_signature"],
            "n_runs": len(rows),
            "mean_keff": statistics.mean(k_values),
            "between_seed_sd_keff": sample_sd(k_values),
            "pooled_within_run_keff_sd": statistics.mean(within),
            "mean_fission_rate_peaking_factor": mean_f,
            "between_seed_sd_fission_peaking_factor": sd_f,
            "fission_peaking_cv_percent": (100.0 * sd_f / mean_f) if sd_f is not None and mean_f else None,
            "min_fission_rate_peaking_factor": min(f_values),
            "max_fission_rate_peaking_factor": max(f_values),
            "fission_peaking_values": ";".join(f"{v:.8f}" for v in f_values),
            "descriptive_rank_by_fission_peaking": None,
        })
    ranked = sorted(summaries, key=lambda r: r["mean_fission_rate_peaking_factor"])
    for rank, row in enumerate(ranked, start=1):
        row["descriptive_rank_by_fission_peaking"] = rank
    report = {
        "schema_version": "1.0",
        "status": "EXPLORATORY_DESCRIPTIVE_ONLY",
        "standard_c5g7_group_boundaries_eV": list(C5G7_GROUP_BOUNDARIES),
        "round_count": len(rounds),
        "candidate_count": len(summaries),
        "run_count": len(run_rows),
        "all_group_structure_audits_passed": True,
        "all_statepoint_hashes_unique": len({r["statepoint_sha256"] for r in run_rows}) == len(run_rows),
        "all_mgxs_hashes_identical": len({r["mgxs_sha256"] for r in run_rows}) == 1,
        "objective": "minimize max(assembly-integrated fission tally) / mean(assembly-integrated fission tally)",
        "objective_interpretation": "dimensionless fission-rate shape proxy, not absolute power or a safety metric",
        "objective_uncertainty": "between-seed sample SD of the derived scalar; three smoke-budget seeds are insufficient for calibrated confidence intervals",
        "acceptance_status": "BLOCKED_NO_DESIGN_SPECIFIC_KEFF_BAND_OR_BENCHMARK_GRADE_CONVERGENCE",
        "no_winner_claim": True,
        "limits": [
            "100 batches, 10 inactive, 1000 particles per batch: smoke settings only.",
            "Three repetitions per layout provide descriptive variability, not strong uncertainty calibration.",
            "The design-specific acceptable k_eff band is not established.",
            "Fission-rate peaking is a relative proxy, not absolute power or a reactor-safety metric.",
            "The legacy fresh/once_burned/twice_burned QUBO still has no defensible mapping to C5G7 UO2/MOX material definitions."
        ],
        "candidate_summary": summaries,
        "run_count_by_round": {round_dir.name: sum(1 for r in run_rows if r["round"] == round_dir.name) for round_dir in rounds}
    }
    return run_rows, summaries, report


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        raise ValueError(f"refusing to write empty CSV: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def render_markdown(report: dict) -> str:
    lines = [
        "# Corrected-group C5G7 fission-peaking repeatability (smoke budget)",
        "",
        f"Status: **{report['status']}**. Runs: {report['run_count']} across {report['round_count']} rounds and {report['candidate_count']} layouts.",
        "",
        "All runs passed the standard C5G7 energy-group audit and used one shared MGXS hash. These are exploratory smoke settings (100 batches, 10 inactive, 1,000 particles per batch), not benchmark-grade convergence.",
        "",
        "| Layout | Mean k_eff | Between-seed SD(k_eff) | Mean fission peaking | Between-seed SD(F) | CV(F) | Descriptive F rank |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in sorted(report["candidate_summary"], key=lambda r: r["descriptive_rank_by_fission_peaking"]):
        lines.append(
            f"| {row['layout_signature']} | {row['mean_keff']:.8f} | {row['between_seed_sd_keff']:.8f} | "
            f"{row['mean_fission_rate_peaking_factor']:.6f} | {row['between_seed_sd_fission_peaking_factor']:.6f} | "
            f"{row['fission_peaking_cv_percent']:.3f}% | {row['descriptive_rank_by_fission_peaking']} |"
        )
    lines += [
        "",
        "## Interpretation limits",
        "",
        "- The peaking factor is a relative assembly-integrated fission-rate proxy, not absolute power and not a safety metric.",
        "- The standard group boundaries correct the prior model-identity error, but the low smoke budget does not establish benchmark convergence.",
        "- Between-seed SD describes variability of the derived scalar across three runs; it is not a calibrated confidence interval.",
        "- The design-specific acceptable k_eff band remains unresolved, so **no layout is recommended or declared a winner**.",
        "- The legacy burnup-state QUBO remains unmapped to C5G7 UO2/MOX materials.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--study-root", required=True, type=Path)
    parser.add_argument("--outdir", required=True, type=Path)
    args = parser.parse_args()
    if args.outdir.exists() and any(args.outdir.iterdir()):
        parser.error(f"refusing to overwrite non-empty output directory: {args.outdir}")
    args.outdir.mkdir(parents=True, exist_ok=True)
    try:
        runs, summaries, report = analyze_study(args.study_root)
    except (OSError, ValueError, KeyError, RuntimeError) as exc:
        parser.error(str(exc))
    write_csv(args.outdir / "run_level_fission_objective.csv", runs)
    write_csv(args.outdir / "fission_objective_repeatability_summary.csv", summaries)
    (args.outdir / "fission_objective_repeatability.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8"
    )
    (args.outdir / "FISSION_OBJECTIVE_REPEATABILITY.md").write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps({"status": report["status"], "run_count": report["run_count"],
                      "candidate_count": report["candidate_count"], "outdir": str(args.outdir)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
