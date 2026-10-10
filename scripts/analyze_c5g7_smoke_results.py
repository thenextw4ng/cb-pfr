#!/usr/bin/env python3
"""Analyze the six C5G7 smoke-run records without making benchmark claims."""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--study-summary", required=True, type=Path)
    parser.add_argument("--outdir", required=True, type=Path)
    args = parser.parse_args()
    summary = json.loads(args.study_summary.read_text(encoding="utf-8"))
    if summary.get("status") != "all_runs_completed_needs_independent_validation":
        parser.error(f"study status is not all-runs-completed: {summary.get('status')}")
    cases = summary.get("cases", [])
    if len(cases) != 6 or any(case.get("status") != "completed" for case in cases):
        parser.error("expected six completed candidate smoke runs")
    args.outdir.mkdir(parents=True, exist_ok=True)
    outputs = ["candidate_summary.csv", "pairwise_keff_comparison.csv", "smoke_analysis.json", "keff_comparison.png", "SMOKE_ANALYSIS.md"]
    for name in outputs:
        if (args.outdir / name).exists():
            parser.error(f"refusing to overwrite {args.outdir / name}")

    rows = []
    mesh_summaries = []
    for case in cases:
        result = case["physical_results"]
        keff = float(result["keff_mean"])
        sd = float(result["keff_std_dev"])
        tallies = result.get("tallies", {})
        aggregate = tallies.get("tally 2", {})
        scores = aggregate.get("scores", [])
        values = np.asarray(aggregate.get("mean", []), dtype=float).reshape(-1)
        sds = np.asarray(aggregate.get("std_dev", []), dtype=float).reshape(-1)
        aggregate_values = {score: float(values[i]) for i, score in enumerate(scores) if i < len(values)}
        aggregate_sds = {score: float(sds[i]) for i, score in enumerate(scores) if i < len(sds)}

        mesh = tallies.get("tally 1", {})
        mesh_scores = mesh.get("scores", [])
        mesh_mean = np.asarray(mesh.get("mean", []), dtype=float)
        mesh_sd = np.asarray(mesh.get("std_dev", []), dtype=float)
        mesh_summary = {"candidate_id": case["candidate_id"], "scores": {}}
        if mesh_mean.size and mesh_mean.shape[-1] == len(mesh_scores):
            flat = mesh_mean.reshape(-1, len(mesh_scores))
            for i, score in enumerate(mesh_scores):
                vals = flat[:, i]
                mesh_summary["scores"][score] = {
                    "n_bins": int(vals.size),
                    "n_positive": int(np.count_nonzero(vals > 0)),
                    "n_zero": int(np.count_nonzero(vals == 0)),
                    "mean_across_mesh_bins": float(np.mean(vals)),
                    "median": float(np.median(vals)),
                    "q95": float(np.percentile(vals, 95)),
                    "max": float(np.max(vals)),
                }
        mesh_summaries.append(mesh_summary)

        pre_hashes = result.get("pre_transport_hashes") or {}
        post_hashes = result.get("post_transport_hashes") or {}
        mgxs_key = "model/2d/mgxs.h5"
        rows.append({
            "candidate_id": case["candidate_id"],
            "layout_signature": case["candidate_id"].split("-")[-1],
            "canonical_reference": bool(case["is_canonical_reference_arrangement"]),
            "seed": case.get("seed"),
            "batches": summary["settings"]["batches"],
            "inactive": summary["settings"]["inactive"],
            "particles_per_batch": summary["settings"]["particles"],
            "keff_mean": keff,
            "keff_std_dev": sd,
            "keff_relative_sd_percent": sd / abs(keff) * 100.0 if keff else None,
            "aggregate_flux_score": aggregate_values.get("flux"),
            "aggregate_fission_score": aggregate_values.get("fission"),
            "aggregate_nu_fission_score": aggregate_values.get("nu-fission"),
            "mgxs_sha256_before_transport": pre_hashes.get(mgxs_key),
            "mgxs_sha256_after_transport": post_hashes.get(mgxs_key),
            "mutated_preexisting_file_count": len(result.get("mutated_preexisting_files") or {}),
            "mutated_preexisting_files": ";".join(sorted((result.get("mutated_preexisting_files") or {}).keys())),
        })

    rows_sorted = sorted(rows, key=lambda row: row["keff_mean"])
    for rank, row in enumerate(rows_sorted, 1):
        row["descriptive_keff_order"] = rank
    with (args.outdir / "candidate_summary.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows_sorted[0].keys()))
        writer.writeheader()
        writer.writerows(rows_sorted)

    pairs = []
    for i, left in enumerate(rows):
        for right in rows[i + 1:]:
            delta = left["keff_mean"] - right["keff_mean"]
            combined_sd = math.sqrt(left["keff_std_dev"] ** 2 + right["keff_std_dev"] ** 2)
            pairs.append({
                "candidate_i": left["candidate_id"],
                "candidate_j": right["candidate_id"],
                "delta_keff_i_minus_j": delta,
                "combined_reported_sd": combined_sd,
                "absolute_delta_over_combined_sd": abs(delta) / combined_sd if combined_sd else None,
                "interpretation": "descriptive standardized difference; not a formal significance test or benchmark acceptance",
            })
    pairs.sort(key=lambda row: row["absolute_delta_over_combined_sd"] or 0, reverse=True)
    with (args.outdir / "pairwise_keff_comparison.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(pairs[0].keys()))
        writer.writeheader()
        writer.writerows(pairs)

    means = np.asarray([row["keff_mean"] for row in rows_sorted], dtype=float)
    stds = np.asarray([row["keff_std_dev"] for row in rows_sorted], dtype=float)
    mgxs_before = sorted({row["mgxs_sha256_before_transport"] for row in rows_sorted if row["mgxs_sha256_before_transport"]})
    mgxs_after = sorted({row["mgxs_sha256_after_transport"] for row in rows_sorted if row["mgxs_sha256_after_transport"]})
    mutated_count = sum(row["mutated_preexisting_file_count"] for row in rows_sorted)
    analysis = {
        "schema_version": "1.0",
        "study_id": summary.get("study_id"),
        "upstream_repository": summary.get("upstream_repository"),
        "upstream_commit": summary.get("upstream_commit"),
        "study_status": summary.get("status"),
        "settings": summary.get("settings"),
        "candidate_count": len(rows_sorted),
        "keff_min_candidate": rows_sorted[0]["candidate_id"],
        "keff_min": float(means.min()),
        "keff_max_candidate": rows_sorted[-1]["candidate_id"],
        "keff_max": float(means.max()),
        "keff_range": float(means.max() - means.min()),
        "keff_range_percent_of_candidate_mean": float((means.max() - means.min()) / means.mean() * 100.0),
        "mgxs_sha256_before_transport_unique": mgxs_before,
        "mgxs_sha256_after_transport_unique": mgxs_after,
        "all_candidates_share_same_pre_transport_mgxs": len(mgxs_before) == 1,
        "all_candidates_share_same_post_transport_mgxs": len(mgxs_after) == 1,
        "mutated_preexisting_file_count_sum": mutated_count,
        "candidate_results_sorted_by_keff_mean": rows_sorted,
        "mesh_tally_summaries": mesh_summaries,
        "pairwise_comparison": pairs,
        "interpretation_limits": [
            "These are low-budget smoke runs (100 batches, 10 inactive, 1,000 particles per batch), not benchmark-grade convergence results.",
            "The six assembly placements are design variants, not all official C5G7 benchmark reference cases.",
            "A numerical ordering by keff is not a recommendation to minimize keff; the optimization objective and physical constraints must be predeclared.",
            "Reported Monte Carlo standard deviations do not quantify model bias or nuclear-data uncertainty.",
            "Check pre-transport versus post-transport MGXS hashes before making cross-run comparisons.",
            "This assembly-placement formulation is separate from the legacy fresh/once_burned/twice_burned QUBO."
        ],
    }
    (args.outdir / "smoke_analysis.json").write_text(json.dumps(analysis, indent=2, allow_nan=False) + "\n", encoding="utf-8")

    fig, ax = plt.subplots(figsize=(10, 6), constrained_layout=True)
    x = np.arange(len(rows_sorted))
    labels = [row["candidate_id"].replace("c5g7-2x2-", "") for row in rows_sorted]
    ax.errorbar(x, means, yerr=stds, fmt="o", capsize=4)
    ax.set_xticks(x, labels, rotation=25, ha="right")
    ax.set_ylabel("Effective multiplication factor, k_eff")
    ax.set_title("C5G7 layout smoke runs — 1 reported SD (not benchmark-grade)")
    ax.grid(True, axis="y", alpha=0.3)
    fig.savefig(args.outdir / "keff_comparison.png", dpi=180)
    plt.close(fig)

    lines = [
        "# C5G7 layout smoke analysis",
        "",
        f"- Upstream commit: `{summary.get('upstream_commit')}`",
        f"- Runs completed: {len(rows_sorted)}/6",
        f"- Settings: {summary['settings']['batches']} batches, {summary['settings']['inactive']} inactive, {summary['settings']['particles']} particles/batch, seeds {summary['settings']['seed_base']}–{summary['settings']['seed_base'] + 5}",
        f"- k_eff range: {means.min():.8f} to {means.max():.8f} (range {means.max()-means.min():.8f}; {analysis['keff_range_percent_of_candidate_mean']:.2f}% of the candidate mean)",
        f"- Pre-transport MGXS hashes: {', '.join(mgxs_before) if mgxs_before else 'not captured'}",
        f"- Post-transport MGXS hashes: {', '.join(mgxs_after) if mgxs_after else 'not captured'}",
        f"- Pre-existing file mutations recorded: {mutated_count}",
        "",
        "| Candidate | Seed | k_eff mean | SD | Relative SD |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in rows_sorted:
        lines.append(f"| {row['candidate_id']} | {row['seed']} | {row['keff_mean']:.8f} | {row['keff_std_dev']:.8f} | {row['keff_relative_sd_percent']:.3f}% |")
    lines += [
        "",
        "## Interpretation",
        "",
        "This is an exploratory smoke test, not benchmark-grade evidence. The numeric k_eff order is descriptive only; it does not identify an optimal or safe layout. The official benchmark reference comparison, a predeclared optimization objective, convergence studies, and model/data verification remain required.",
        "",
        "Do not compare these candidate values directly to the archived production baseline unless the pre-transport cross-section hash and model geometry are confirmed to match. A statepoint being readable does not validate the model.",
    ]
    (args.outdir / "SMOKE_ANALYSIS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({
        "candidate_count": len(rows_sorted),
        "keff_range": [float(means.min()), float(means.max())],
        "range_percent_of_candidate_mean": analysis["keff_range_percent_of_candidate_mean"],
        "mgxs_before": mgxs_before,
        "mgxs_after": mgxs_after,
        "mutated_preexisting_file_count_sum": mutated_count,
        "outdir": str(args.outdir),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
