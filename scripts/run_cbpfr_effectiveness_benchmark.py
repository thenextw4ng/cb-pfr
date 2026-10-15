#!/usr/bin/env python3
"""Prespecified fixed-budget synthetic test of CB-PFR selection value.

This benchmark is synthetic only. Candidate truth is never passed to ranking
methods. Every method sees the same candidate pool and noisy observations.
Failure to demonstrate superiority is a valid scientific result.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import random
import statistics
from pathlib import Path
from typing import Any

from cbpfr.qubo import BURNUP_LABELS, CoreSpec, build_usmanov_style_qubo, enumerate_feasible_candidates
from cbpfr.ranking import MetricLimit, PhysicalEstimate, rank_all_methods
from cbpfr.experiments import require_equal_evaluation_budget

METHODS = ("qubo_only", "point_estimate", "cb_pfr", "uniform_margin")
METRIC_NAME = "synthetic_response"
CALIBRATED_REGIMES = {"calibrated_low", "calibrated_moderate", "calibrated_high"}


def fresh_ring_pairs(model, candidate) -> int:
    decoded = model.decode(candidate.vector)
    return sum(
        decoded[left] == BURNUP_LABELS[0] and decoded[right] == BURNUP_LABELS[0]
        for left, right in model.spec.edges
        if left in model.spec.boundary and right in model.spec.boundary
    )


def arrangement_indicator(model, candidate) -> int:
    decoded = model.decode(candidate.vector)
    return sum(
        index + 1 for index, position in enumerate(model.spec.positions)
        if decoded[position] == BURNUP_LABELS[0]
    ) % 2


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError(f"refusing to create empty CSV: {path.name}")
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def percentile(sorted_values: list[float], probability: float) -> float:
    index = int(math.floor(probability * (len(sorted_values) - 1)))
    return sorted_values[index]


def bootstrap_mean_ci(differences: list[int], *, seed: int, resamples: int = 5000) -> tuple[float, float]:
    """Pool-level paired percentile bootstrap for binary outcome differences."""
    if not differences:
        raise ValueError("bootstrap requires paired pools")
    rng = random.Random(seed)
    n = len(differences)
    estimates = []
    for _ in range(resamples):
        sample_sum = 0
        for _ in range(n):
            sample_sum += differences[rng.randrange(n)]
        estimates.append(sample_sum / n)
    estimates.sort()
    return percentile(estimates, 0.025), percentile(estimates, 0.975)


def wilson_interval(successes: int, n: int, z: float = 1.959963984540054) -> tuple[float, float]:
    if n <= 0:
        raise ValueError("Wilson interval requires n > 0")
    p = successes / n
    denom = 1.0 + z * z / n
    center = (p + z * z / (2.0 * n)) / denom
    half = z * math.sqrt(p * (1.0 - p) / n + z * z / (4.0 * n * n)) / denom
    return max(0.0, center - half), min(1.0, center + half)


def make_metric(protocol: dict[str, Any]) -> MetricLimit:
    return MetricLimit(
        name=METRIC_NAME,
        upper=float(protocol["synthetic_truth"]["upper_feasibility_limit"]),
        z=float(protocol["fixed_method_parameters"]["cb_pfr_z"]),
        scale=0.01,
        weight=1.0,
        uncertainty_kind="reported_sigma_in_synthetic_data_generator",
        units="synthetic units",
        bound_kind="operational_heuristic",
    )


def make_pool(*, model, candidates, protocol, regime, seed, pool_id, role):
    """Only returned estimates go to selection; truth remains evaluator-side."""
    rng = random.Random(seed)
    pool = rng.sample(candidates, int(protocol["confirmation"]["candidate_pool_size"]))
    truth_config = protocol["synthetic_truth"]
    estimates: dict[str, PhysicalEstimate] = {}
    truth: dict[str, float] = {}
    observation_rows = []
    truth_rows = []
    for candidate in pool:
        pair_count = fresh_ring_pairs(model, candidate)
        indicator = arrangement_indicator(model, candidate)
        latent = (
            float(truth_config["response_base"])
            + float(truth_config["fresh_ring_pair_increment"]) * pair_count
            + float(truth_config["arrangement_indicator_increment"]) * indicator
            + float(regime["latent_offset"])
        )
        sigma = float(regime["high_sigma"] if indicator else regime["low_sigma"])
        noise = rng.gauss(0.0, sigma)
        if regime["noise_model"] == "gaussian_with_5pct_3sigma_contamination":
            if rng.random() < 0.05:
                noise += rng.choice((-1.0, 1.0)) * 3.0 * sigma
        elif regime["noise_model"] != "gaussian":
            raise ValueError(f"unknown noise model: {regime['noise_model']}")
        observed = latent + noise
        reported_sigma = sigma * float(regime["uncertainty_report_fraction"])
        if not all(math.isfinite(v) for v in (latent, observed, reported_sigma)) or reported_sigma <= 0:
            raise ValueError("invalid generated observation or uncertainty")
        cid = candidate.candidate_id
        estimates[cid] = PhysicalEstimate(cid, {METRIC_NAME: (observed, reported_sigma)})
        truth[cid] = latent
        observation_rows.append({
            "role": role, "pool_id": pool_id, "seed": seed, "regime": regime["id"],
            "candidate_id": cid, "observed_response": observed,
            "reported_uncertainty": reported_sigma,
            "physical_evaluation_budget_per_method": len(pool),
            "data_kind": "synthetic", "physical_simulation_performed": False,
        })
        truth_rows.append({
            "role": role, "pool_id": pool_id, "seed": seed, "regime": regime["id"],
            "candidate_id": cid, "latent_true_response": latent,
            "true_noise_sigma": sigma,
            "true_feasible": latent <= float(truth_config["upper_feasibility_limit"]),
            "evaluator_only": True,
        })
    return pool, estimates, truth, observation_rows, truth_rows


def select_all(model, pool, estimates, metric, uniform_margin):
    budgets = {method: len(pool) for method in METHODS}
    require_equal_evaluation_budget(budgets, expected=len(pool))
    rankings = rank_all_methods(model, pool, estimates, [metric], {METRIC_NAME: uniform_margin})
    selected = {}
    for method in METHODS:
        winner = rankings[method][0]
        assessment = winner.physical
        selected[method] = {
            "candidate_id": winner.candidate.candidate_id,
            "predicted_feasible": None if assessment is None else assessment.indicator == 0,
            "predicted_violation": None if assessment is None else assessment.aggregate_violation,
            "qubo_energy": winner.qubo_energy,
            "evaluation_budget": len(pool),
        }
    if len({item["evaluation_budget"] for item in selected.values()}) != 1:
        raise RuntimeError("methods were not evaluated under equal budgets")
    return selected


def tune_uniform_margin(*, model, candidates, protocol, metric):
    development = protocol["development"]
    regime = next(item for item in protocol["confirmation"]["regimes"] if item["id"] == development["regime"])
    pool_cache = []
    obs_rows, truth_rows = [], []
    for idx in range(int(development["pools"])):
        seed = int(development["seed_base"]) + idx
        pool_id = f"DEV-{idx:04d}"
        pool, estimates, truth, obs, truth_part = make_pool(
            model=model, candidates=candidates, protocol=protocol, regime=regime,
            seed=seed, pool_id=pool_id, role="development",
        )
        pool_cache.append((pool, estimates, truth))
        obs_rows.extend(obs)
        truth_rows.extend(truth_part)
    tuning = []
    for raw_margin in development["uniform_margin_grid"]:
        margin = float(raw_margin)
        successes = 0
        for pool, estimates, truth in pool_cache:
            result = rank_all_methods(model, pool, estimates, [metric], {METRIC_NAME: margin})
            cid = result["uniform_margin"][0].candidate.candidate_id
            successes += int(truth[cid] <= float(protocol["synthetic_truth"]["upper_feasibility_limit"]))
        tuning.append({
            "regime": regime["id"], "margin": margin, "development_pools": len(pool_cache),
            "feasible_selections": successes, "feasible_selection_rate": successes / len(pool_cache),
            "selection_rule": "maximize development rate; ties choose smaller margin",
        })
    best = max(tuning, key=lambda row: (row["feasible_selection_rate"], -row["margin"]))
    for row in tuning:
        row["selected_for_confirmation"] = row["margin"] == best["margin"]
    return float(best["margin"]), tuning, obs_rows, truth_rows


def paired_effect(regime, cb, baseline, baseline_name, seed):
    if len(cb) != len(baseline):
        raise ValueError("paired outcomes must have equal lengths")
    differences = [int(x) - int(y) for x, y in zip(cb, baseline)]
    low, high = bootstrap_mean_ci(differences, seed=seed)
    cb_only = sum(x and not y for x, y in zip(cb, baseline))
    baseline_only = sum((not x) and y for x, y in zip(cb, baseline))
    return {
        "regime": regime["id"], "regime_role": regime["role"],
        "comparison": f"cb_pfr_minus_{baseline_name}", "pools": len(cb),
        "cb_pfr_feasible_selections": sum(cb), "baseline_feasible_selections": sum(baseline),
        "paired_rate_difference": sum(differences) / len(differences),
        "paired_bootstrap_95_low": low, "paired_bootstrap_95_high": high,
        "cb_pfr_only_success": cb_only, "baseline_only_success": baseline_only,
        "paired_ties": len(cb) - cb_only - baseline_only,
        "bootstrap_resamples": 5000, "bootstrap_seed": seed,
        "superiority_supported_for_this_comparison": low > 0.0,
    }


def report_markdown(payload, method_rows, paired_rows):
    lines = [
        "# CB-PFR fixed-budget synthetic effectiveness benchmark", "",
        f"Run status: {payload['run_status']}",
        f"Scientific decision: {payload['scientific_decision']}", "",
        "This is a synthetic method benchmark only. It is not an OpenMC run, C5G7/BEAVRS validation, a reactor-safety claim, or evidence of quantum advantage.", "",
        "## Development split", "",
        f"- Development pools: {payload['development_pools']}",
        f"- Frozen uniform-margin baseline: {payload['selected_uniform_margin']}",
        "- Development pools are excluded from confirmatory effect estimates.", "",
        "## Confirmatory feasible-selection rates", "",
        "| Regime | Method | Feasible / pools | Rate | Wilson 95% interval |",
        "|---|---|---:|---:|---:|",
    ]
    for row in method_rows:
        lines.append(
            f"| {row['regime']} | {row['method']} | {row['feasible_selections']} / {row['pools']} | "
            f"{row['feasible_selection_rate']:.4f} | [{row['wilson95_low']:.4f}, {row['wilson95_high']:.4f}] |"
        )
    lines.extend(["", "## Paired effects: CB-PFR minus baseline", "",
                  "| Regime | Baseline | Difference | Paired bootstrap 95% interval | CB-PFR-only | Baseline-only |",
                  "|---|---|---:|---:|---:|---:|"])
    for row in paired_rows:
        baseline = row["comparison"].replace("cb_pfr_minus_", "")
        lines.append(
            f"| {row['regime']} | {baseline} | {row['paired_rate_difference']:+.4f} | "
            f"[{row['paired_bootstrap_95_low']:+.4f}, {row['paired_bootstrap_95_high']:+.4f}] | "
            f"{row['cb_pfr_only_success']} | {row['baseline_only_success']} |"
        )
    lines.extend([
        "", "## Interpretation", "", payload["interpretation"], "",
        "All methods received the same candidate pool and noisy observation table, with a fixed budget of 12 candidate evaluations per method per pool. The evaluator kept latent truth in a separate output table and joined it only after selection. The candidate pool is the independent unit for paired inference.",
        "", "Stress regimes (under-reported uncertainty, contaminated noise, and no truly feasible candidate) are diagnostic only and do not contribute to the primary superiority gate.",
        "", "## Limitations", "",
        "- The latent responses and noise are artificial and do not reproduce OpenMC physics.",
        "- The current CB-PFR uncertainty width is an operational heuristic, not a generally calibrated confidence interval.",
        "- A favorable result only supports a claim about this frozen synthetic generator.",
        "- A failed gate means this experiment did not demonstrate the predeclared advantage; it does not prove CB-PFR can never help.",
        "", "## Reproduction", "",
        "Run python scripts/run_cbpfr_effectiveness_benchmark.py --outdir /tmp/cbpfr-effectiveness on the frozen protocol branch.",
    ])
    return "\n".join(lines) + "\n"


def run(protocol_path: Path, outdir: Path):
    if outdir.exists() and any(outdir.iterdir()):
        raise FileExistsError(f"refusing to overwrite nonempty output directory: {outdir}")
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    expected_id = "CBPFR-FIXED-BUDGET-SYNTHETIC-EFFECTIVENESS-2026-10-15"
    if protocol.get("protocol_id") != expected_id:
        raise ValueError("unexpected frozen protocol ID")
    core_path = protocol_path.parents[1] / "toy_core_7.json"
    if not core_path.is_file():
        raise FileNotFoundError(f"toy core JSON is missing: {core_path}")
    model = build_usmanov_style_qubo(CoreSpec.from_json(core_path))
    candidates = enumerate_feasible_candidates(model)
    sample_size = int(protocol["confirmation"]["candidate_pool_size"])
    if len(candidates) < sample_size:
        raise RuntimeError("candidate space smaller than the requested pool")
    metric = make_metric(protocol)
    selected_margin, tuning_rows, dev_obs, dev_truth = tune_uniform_margin(
        model=model, candidates=candidates, protocol=protocol, metric=metric,
    )
    observation_rows = list(dev_obs)
    truth_rows = list(dev_truth)
    selection_rows, method_rows, paired_rows = [], [], []

    regimes = protocol["confirmation"]["regimes"]
    for regime_index, regime in enumerate(regimes):
        outcome_by_method = {method: [] for method in METHODS}
        predicted_by_method = {method: [] for method in METHODS}
        latent_by_method = {method: [] for method in METHODS}
        seed_base = int(protocol["confirmation"]["seed_base"]) + regime_index * 1_000_000
        for pool_index in range(int(protocol["confirmation"]["pools_per_regime"])):
            seed = seed_base + pool_index
            pool_id = f"{regime['id']}-{pool_index:04d}"
            pool, estimates, truth, obs, truth_part = make_pool(
                model=model, candidates=candidates, protocol=protocol, regime=regime,
                seed=seed, pool_id=pool_id, role="confirmatory",
            )
            observation_rows.extend(obs)
            truth_rows.extend(truth_part)
            selected = select_all(model, pool, estimates, metric, selected_margin)
            if {v["evaluation_budget"] for v in selected.values()} != {sample_size}:
                raise RuntimeError("fixed-budget equality assertion failed")
            limit = float(protocol["synthetic_truth"]["upper_feasibility_limit"])
            for method in METHODS:
                item = selected[method]
                latent = truth[item["candidate_id"]]
                feasible = latent <= limit
                outcome_by_method[method].append(feasible)
                predicted_by_method[method].append(item["predicted_feasible"])
                latent_by_method[method].append(latent)
                selection_rows.append({
                    "pool_id": pool_id, "seed": seed, "regime": regime["id"],
                    "regime_role": regime["role"], "method": method,
                    "selected_candidate_id": item["candidate_id"],
                    "selected_latent_true_response": latent,
                    "selected_true_feasible": feasible,
                    "selected_predicted_feasible": item["predicted_feasible"],
                    "selected_predicted_violation": item["predicted_violation"],
                    "selected_qubo_energy": item["qubo_energy"],
                    "physical_evaluation_budget": item["evaluation_budget"],
                })
        n = int(protocol["confirmation"]["pools_per_regime"])
        for method in METHODS:
            outcomes = outcome_by_method[method]
            successes = sum(outcomes)
            low, high = wilson_interval(successes, n)
            predicted = predicted_by_method[method]
            available = [(p, y) for p, y in zip(predicted, outcomes) if p is not None]
            false_rate = (
                sum(bool(p) and not y for p, y in available) / len(available)
                if available else None
            )
            method_rows.append({
                "regime": regime["id"], "regime_role": regime["role"], "method": method,
                "pools": n, "feasible_selections": successes,
                "feasible_selection_rate": successes / n,
                "wilson95_low": low, "wilson95_high": high,
                "false_feasible_rate_when_method_reports_feasibility": false_rate,
                "mean_selected_latent_response": statistics.mean(latent_by_method[method]),
                "evaluation_budget_per_pool": sample_size,
            })
        for comparison_index, baseline in enumerate(("point_estimate", "uniform_margin")):
            paired_rows.append(paired_effect(
                regime, outcome_by_method["cb_pfr"], outcome_by_method[baseline],
                baseline, seed=20263015 + regime_index * 100 + comparison_index,
            ))

    primary = [row for row in paired_rows if row["regime"] in CALIBRATED_REGIMES]
    gate_pass = bool(primary) and all(row["paired_bootstrap_95_low"] > 0.0 for row in primary)
    decision = (
        "SYNTHETIC_SUPERIORITY_GATE_MET_FOR_FROZEN_PROTOCOL_ONLY"
        if gate_pass else "NO_SYNTHETIC_SUPERIORITY_DEMONSTRATED"
    )
    interpretation = (
        "The predeclared synthetic superiority gate was met in all calibrated Gaussian regimes. "
        "This is limited to the frozen synthetic generator and is not physical validation."
        if gate_pass else
        "The predeclared synthetic superiority gate was not met in every calibrated Gaussian regime. "
        "Report the observed paired effects and intervals without claiming general incremental "
        "selection advantage. Stress regimes do not rescue the primary gate."
    )
    payload = {
        "schema_version": "1.0",
        "protocol_id": protocol["protocol_id"],
        "run_status": "COMPLETED_INTEGRITY_CHECKS_PENDING_EXTERNAL_REVIEW",
        "scientific_decision": decision,
        "interpretation": interpretation,
        "protocol_sha256": hashlib.sha256(protocol_path.read_bytes()).hexdigest(),
        "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "git_commit": os.environ.get("GITHUB_SHA", "local_unpinned"),
        "development_pools": int(protocol["development"]["pools"]),
        "selected_uniform_margin": selected_margin,
        "candidate_count_in_space": len(candidates),
        "candidate_pool_size": sample_size,
        "confirmatory_pools_per_regime": int(protocol["confirmation"]["pools_per_regime"]),
        "regime_count": len(regimes),
        "confirmatory_pool_count": len(regimes) * int(protocol["confirmation"]["pools_per_regime"]),
        "confirmatory_selection_rows": len(selection_rows),
        "candidate_observation_rows": len(observation_rows),
        "evaluator_truth_rows": len(truth_rows),
        "same_pool_and_observations_for_all_methods": True,
        "equal_fixed_budget_asserted": True,
        "truth_table_kept_separate_until_after_selection": True,
        "primary_superiority_gate_met": gate_pass,
        "primary_regimes": sorted(CALIBRATED_REGIMES),
        "stress_regimes_excluded_from_primary_gate": [
            item["id"] for item in regimes if item["id"] not in CALIBRATED_REGIMES
        ],
        "physical_validation": False,
        "official_benchmark_acceptance": False,
        "quantum_hardware_run": False,
    }

    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "protocol_snapshot.json").write_text(
        json.dumps(protocol, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    write_csv(outdir / "candidate_observations.csv", observation_rows)
    write_csv(outdir / "evaluator_truth.csv", truth_rows)
    write_csv(outdir / "development_margin_tuning.csv", tuning_rows)
    write_csv(outdir / "pool_method_selections.csv", selection_rows)
    write_csv(outdir / "method_summary.csv", method_rows)
    write_csv(outdir / "paired_effects.csv", paired_rows)
    (outdir / "summary.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (outdir / "report.md").write_text(
        report_markdown(payload, method_rows, paired_rows), encoding="utf-8"
    )
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--protocol",
        type=Path,
        default=Path("config/benchmarks/cbpfr_effectiveness_protocol_2026-10-15.json"),
    )
    parser.add_argument("--outdir", type=Path, required=True)
    args = parser.parse_args()
    payload = run(args.protocol, args.outdir)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
