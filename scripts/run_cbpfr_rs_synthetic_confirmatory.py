#!/usr/bin/env python3
"""Locked synthetic CB-PFR-vs-R&S benchmark; not a physical reactor model."""
from __future__ import annotations
import csv, hashlib, json, platform
from pathlib import Path
import numpy as np
from scipy.stats import binomtest

SEED = 20261013
POOLS = 10_000
N_CANDIDATES = 12
THRESHOLD = 0.98
Z = 1.96
UNIFORM_MARGIN = 0.008
SCENARIOS = ("calibrated_heteroscedastic", "calibrated_homoscedastic",
             "underreported_uncertainty_50pct", "shifted_near_threshold")
METHODS = ("point_estimate_rs", "cb_pfr", "uniform_margin")

def generate(rng: np.random.Generator, scenario: str):
    n, k = POOLS, N_CANDIDATES
    if scenario == "shifted_near_threshold":
        theta = 0.965 + 0.030 * rng.beta(2.0, 2.0, size=(n, k))
        sigma = np.full((n, k), 0.006)
        estimate = theta + 0.008 + rng.normal(0.0, sigma)
        reported = sigma.copy()
    else:
        theta = 0.94 + 0.07 * rng.beta(3.0, 3.0, size=(n, k))
        if scenario == "calibrated_homoscedastic":
            sigma = np.full((n, k), 0.007)
        else:
            sigma = np.where(rng.random((n, k)) < 0.5, 0.004, 0.010)
        estimate = theta + rng.normal(0.0, sigma)
        reported = sigma * (0.5 if scenario == "underreported_uncertainty_50pct" else 1.0)
    return theta, estimate, reported, sigma

def select(estimate, reported, method):
    if method == "point_estimate_rs":
        declared = estimate >= THRESHOLD
        score = estimate
    elif method == "cb_pfr":
        score = estimate - Z * reported
        declared = score >= THRESHOLD
    elif method == "uniform_margin":
        score = estimate - UNIFORM_MARGIN
        declared = score >= THRESHOLD
    else:
        raise ValueError(method)
    # Prefer the highest observed estimate among candidates passing the method's screen.
    # If no candidate passes, fall back to the highest method-specific score.
    chosen = np.empty(estimate.shape[0], dtype=int)
    for i in range(estimate.shape[0]):
        eligible = np.flatnonzero(declared[i])
        chosen[i] = eligible[np.argmax(estimate[i, eligible])] if len(eligible) else int(np.argmax(score[i]))
    return chosen, declared

def metrics(theta, estimate, reported, method, chosen, declared):
    row = np.arange(theta.shape[0])
    selected_true = theta[row, chosen] >= THRESHOLD
    selected_declared = declared[row, chosen]
    feasible = theta >= THRESHOLD
    any_feasible = feasible.any(axis=1)
    best_feasible = np.max(np.where(feasible, theta, -np.inf), axis=1)
    selected_theta = theta[row, chosen]
    regret = np.full(len(row), np.nan)
    regret[any_feasible] = best_feasible[any_feasible] - selected_theta[any_feasible]
    lower = estimate - Z * reported
    covered = theta >= lower
    return {
        "selected_true_feasibility_rate": float(selected_true.mean()),
        "selected_true_feasible_count": int(selected_true.sum()),
        "selected_declared_feasible_rate": float(selected_declared.mean()),
        "false_feasible_rate_among_declared": float(((~selected_true) & selected_declared).sum() / max(1, selected_declared.sum())),
        "pool_has_feasible_candidate_rate": float(any_feasible.mean()),
        "feasible_best_selection_rate_given_feasible_pool": float(
            (selected_true & np.isclose(selected_theta, best_feasible, atol=1e-12))[any_feasible].mean()
        ) if any_feasible.any() else None,
        "mean_regret_given_feasible_pool": float(np.nanmean(regret)) if any_feasible.any() else None,
        "nominal_95pct_lower_bound_empirical_coverage": float(covered.mean()),
        "fallback_selection_count": int((~declared[row, chosen]).sum())
    }

def paired_stats(a: np.ndarray, b: np.ndarray, rng: np.random.Generator, reps=3000):
    # paired binary outcomes; bootstrap resamples independent pools
    diff = a.astype(float) - b.astype(float)
    boots = np.empty(reps)
    n = len(diff)
    for j in range(reps):
        boots[j] = diff[rng.integers(0, n, size=n)].mean()
    ci = np.quantile(boots, [0.025, 0.975])
    a_wins = int(((a == 1) & (b == 0)).sum())
    b_wins = int(((a == 0) & (b == 1)).sum())
    p = float(binomtest(min(a_wins, b_wins), a_wins + b_wins, 0.5, alternative="two-sided").pvalue) if a_wins+b_wins else 1.0
    return {"difference": float(diff.mean()), "bootstrap_95pct_ci": [float(ci[0]), float(ci[1])],
            "cbpfr_wins": a_wins, "baseline_wins": b_wins, "exact_mcnemar_p_raw": p}

def holm(pvals):
    order = sorted(pvals, key=pvals.get)
    out, running = {}, 0.0
    m = len(order)
    for rank, key in enumerate(order):
        adj = min(1.0, (m-rank)*pvals[key])
        running = max(running, adj)
        out[key] = running
    return out

def main():
    outdir = Path("results/fixed_budget_ranking_selection_confirmatory")
    outdir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(SEED)
    records = []
    scenario_outcomes = {}
    summaries = {}
    pooled_outcomes = {m: [] for m in METHODS}
    for sidx, scenario in enumerate(SCENARIOS):
        # Deterministic, scenario-specific RNG stream.
        srng = np.random.default_rng(SEED + 1009 * (sidx + 1))
        theta, estimate, reported, true_sigma = generate(srng, scenario)
        declared_map, selected_map, outcome_map = {}, {}, {}
        for method in METHODS:
            chosen, declared = select(estimate, reported, method)
            selected_map[method] = chosen
            declared_map[method] = declared
            outcome_map[method] = (theta[np.arange(POOLS), chosen] >= THRESHOLD).astype(np.int8)
            summaries.setdefault(scenario, {})[method] = metrics(theta, estimate, reported, method, chosen, declared)
            pooled_outcomes[method].append(outcome_map[method])
            for i in range(POOLS):
                records.append({
                    "scenario": scenario, "pool_id": i, "candidate_count": N_CANDIDATES,
                    "method": method, "selected_candidate_index": int(chosen[i]),
                    "selected_latent_response": float(theta[i, chosen[i]]),
                    "selected_observed_estimate": float(estimate[i, chosen[i]]),
                    "selected_reported_se": float(reported[i, chosen[i]]),
                    "selected_true_feasible": int(theta[i, chosen[i]] >= THRESHOLD),
                    "method_declared_feasible": int(declared[i, chosen[i]]),
                    "pool_has_any_feasible_candidate": int(np.any(theta[i] >= THRESHOLD))
                })
        for baseline in ("point_estimate_rs", "uniform_margin"):
            scenario_outcomes.setdefault(scenario, {})[baseline] = paired_stats(
                outcome_map["cb_pfr"], outcome_map[baseline], np.random.default_rng(SEED + sidx*100 + (1 if baseline=="point_estimate_rs" else 2)))
    # Pooled primary analysis, stratified by scenario through concatenation of equal-sized scenario sets.
    pooled = {m: np.concatenate(v) for m, v in pooled_outcomes.items()}
    primary = {b: paired_stats(pooled["cb_pfr"], pooled[b], np.random.default_rng(SEED + 700 + j))
               for j, b in enumerate(("point_estimate_rs", "uniform_margin"))}
    adjusted = holm({k: v["exact_mcnemar_p_raw"] for k, v in primary.items()})
    for k in primary:
        primary[k]["holm_adjusted_p"] = adjusted[k]
        primary[k]["preregistered_advantage_criteria_pass"] = bool(
            primary[k]["difference"] >= 0.02 and primary[k]["bootstrap_95pct_ci"][0] > 0 and adjusted[k] < 0.05
        )
    advantage = all(v["preregistered_advantage_criteria_pass"] for v in primary.values())
    csv_path = outdir / "per_pool_selection_records.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(records[0].keys()))
        writer.writeheader(); writer.writerows(records)
    csv_hash = hashlib.sha256(csv_path.read_bytes()).hexdigest()
    payload = {
        "study_id": "cbpfr_rs_synthetic_confirmatory_v1",
        "status": "EXECUTED_SYNTHETIC_ONLY_NOT_PHYSICAL_VALIDATION",
        "seed": SEED, "pools_per_scenario": POOLS, "candidates_per_pool": N_CANDIDATES,
        "scenario_names": list(SCENARIOS), "threshold": THRESHOLD, "cbpfr_z": Z,
        "uniform_margin": UNIFORM_MARGIN, "primary_endpoint": "selected true-feasibility rate",
        "methods": list(METHODS), "scenario_metrics": summaries, "scenario_paired_comparisons": scenario_outcomes,
        "pooled_primary_comparisons": primary,
        "prespecified_synthetic_advantage_supported": advantage,
        "decision_rule": "CB-PFR must improve feasibility by >=2 percentage points with paired-bootstrap 95% CI above zero and Holm-adjusted McNemar p<0.05 against both baselines.",
        "caveats": [
            "Synthetic benchmark only; does not establish physical or reactor effectiveness.",
            "The DGP family is prespecified but still stylized; inference is conditional on these scenarios.",
            "The R&S baseline here is point-estimate selection under a fixed candidate pool, not adaptive sequential allocation.",
            "Nominal lower-bound coverage is evaluated against generated latent values; it is not a physical-model validation."
        ],
        "reproducibility": {
            "python": platform.python_version(), "numpy": np.__version__,
            "raw_csv": str(csv_path), "raw_csv_sha256": csv_hash,
            "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        }
    }
    json_path = outdir / "confirmatory_summary.json"
    json_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    print(f"SUMMARY_JSON={json_path}")
    print(f"RAW_CSV={csv_path}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
