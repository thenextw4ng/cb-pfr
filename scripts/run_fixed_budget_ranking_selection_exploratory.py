#!/usr/bin/env python3
"""Lightweight exploratory fixed-budget ranking-selection benchmark.

Standard-library only. This is a toy synthetic data-generating process, not
reactor/transport validation and not the confirmatory preregistered experiment.
"""
from __future__ import annotations
import argparse, csv, json, random, statistics
from math import sqrt
from pathlib import Path

METHODS = ("qubo_only", "point_estimate", "cb_pfr", "uniform_margin")

def run(seed: int, pools: int, pool_size: int, limit: float, z: float, uniform_margin: float):
    rng = random.Random(seed)
    rows = []
    for pool_i in range(pools):
        candidates = []
        for j in range(pool_size):
            arrangement = rng.randrange(2)
            fresh_pairs = rng.randrange(3)
            se = 0.004 if arrangement == 0 else 0.010
            latent = 0.954 + 0.013 * fresh_pairs + 0.002 * arrangement
            observed = latent + rng.gauss(0.0, se)
            candidates.append({
                "id": f"p{pool_i:04d}_c{j:02d}", "latent": latent,
                "estimate": observed, "se": se, "qubo_energy": rng.random()
            })
        for method in METHODS:
            scored = []
            for idx, c in enumerate(candidates):
                if method == "qubo_only":
                    key = (c["qubo_energy"], idx)
                else:
                    width = {
                        "point_estimate": 0.0,
                        "cb_pfr": z * c["se"],
                        "uniform_margin": uniform_margin,
                    }[method]
                    violation = max(0.0, c["estimate"] + width - limit)
                    fails = int(violation > 0.0)
                    # Mirrors CB-PFR's physical-feasibility / violation / energy
                    # ordering for a pool whose QUBO-feasibility status is equal.
                    key = (fails, violation / 0.01, c["qubo_energy"], idx)
                scored.append((key, c))
            selected = sorted(scored, key=lambda item: item[0])[0][1]
            rows.append({
                "pool": pool_i, "seed": seed + pool_i, "method": method,
                "candidate_id": selected["id"],
                "latent_true_response": selected["latent"],
                "true_feasible": int(selected["latent"] <= limit),
                "observed_estimate": selected["estimate"],
                "reported_se": selected["se"],
                "evaluation_budget": pool_size,
                "not_physical_validation": True,
            })
    aggregate = {}
    outcomes = {}
    for method in METHODS:
        selected = [r for r in rows if r["method"] == method]
        outcomes[method] = {int(r["pool"]): int(r["true_feasible"]) for r in selected}
        aggregate[method] = {
            "pools": len(selected),
            "pool_size": pool_size,
            "selected_true_feasibility_rate": sum(r["true_feasible"] for r in selected) / len(selected),
            "mean_selected_latent_response": statistics.mean(r["latent_true_response"] for r in selected),
        }
    paired = {}
    for baseline in ("point_estimate", "uniform_margin", "qubo_only"):
        diffs = [outcomes["cb_pfr"][i] - outcomes[baseline][i] for i in range(pools)]
        mean = statistics.mean(diffs)
        se = statistics.stdev(diffs) / sqrt(pools) if pools > 1 else 0.0
        paired[baseline] = {
            "paired_feasibility_rate_difference": mean,
            "normal_approx_95pct_interval": [mean - 1.96 * se, mean + 1.96 * se],
            "cb_pfr_feasible_baseline_infeasible": sum(outcomes["cb_pfr"][i] == 1 and outcomes[baseline][i] == 0 for i in range(pools)),
            "cb_pfr_infeasible_baseline_feasible": sum(outcomes["cb_pfr"][i] == 0 and outcomes[baseline][i] == 1 for i in range(pools)),
        }
    return rows, {
        "study_id": "cbpfr_fixed_budget_ranking_selection_exploratory_simple_run_v1",
        "status": "exploratory_run_completed",
        "seed": seed, "independent_pools": pools, "candidates_per_pool": pool_size,
        "feasibility_threshold": limit, "cbpfr_z": z, "uniform_margin": uniform_margin,
        "methods": list(METHODS), "synthetic_only": True,
        "physical_validation": "NOT_ESTABLISHED",
        "aggregate": aggregate, "paired_cbpfr_minus_baseline": paired,
        "interpretation": (
            "Exploratory result under this explicitly constructed toy data-generating process only. "
            "Not confirmatory evidence, not reactor/transport validation, and not evidence of general superiority. "
            "Intervals are simple normal approximations and should not replace a preregistered confirmatory analysis."
        ),
    }

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=20261011)
    parser.add_argument("--pools", type=int, default=200)
    parser.add_argument("--pool-size", type=int, default=12)
    parser.add_argument("--limit", type=float, default=0.98)
    parser.add_argument("--z", type=float, default=1.96)
    parser.add_argument("--uniform-margin", type=float, default=0.008)
    parser.add_argument("--outdir", type=Path, default=Path("results/fixed_budget_ranking_selection_exploratory"))
    args = parser.parse_args()
    args.outdir.mkdir(parents=True, exist_ok=True)
    rows, summary = run(args.seed, args.pools, args.pool_size, args.limit, args.z, args.uniform_margin)
    with (args.outdir / "per_pool_results.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    (args.outdir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))

if __name__ == "__main__":
    main()
