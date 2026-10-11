#!/usr/bin/env python3
"""Build a new one-hot QUBO over evaluated C5G7 layouts.

This is a C5G7-specific candidate-selection reformulation, not a mapping of the
legacy fresh/once_burned/twice_burned variables. A design-specific k_eff band is
required; without a feasible candidate the script refuses to emit a selectable QUBO.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


REQUIRED_COLUMNS = {
    "candidate_id",
    "layout_signature",
    "mean_keff",
    "between_seed_sd_keff",
    "mean_fission_rate_peaking_factor",
    "between_seed_sd_fission_peaking_factor",
}


def load_candidates(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError("candidate summary CSV is empty")
    missing = REQUIRED_COLUMNS - set(rows[0])
    if missing:
        raise ValueError(f"candidate summary lacks required columns: {sorted(missing)}")
    candidates = []
    seen = set()
    for row in rows:
        cid = row["candidate_id"]
        if cid in seen:
            raise ValueError(f"duplicate candidate_id: {cid}")
        seen.add(cid)
        parsed = {
            "candidate_id": cid,
            "layout_signature": row["layout_signature"],
            "mean_keff": float(row["mean_keff"]),
            "between_seed_sd_keff": float(row["between_seed_sd_keff"]),
            "mean_fission_rate_peaking_factor": float(row["mean_fission_rate_peaking_factor"]),
            "between_seed_sd_fission_peaking_factor": float(row["between_seed_sd_fission_peaking_factor"]),
            "n_runs": int(row.get("n_runs", 0)),
        }
        for key, value in parsed.items():
            if isinstance(value, float) and not __import__("math").isfinite(value):
                raise ValueError(f"{cid}: non-finite {key}")
        if parsed["between_seed_sd_keff"] < 0 or parsed["between_seed_sd_fission_peaking_factor"] < 0:
            raise ValueError(f"{cid}: standard deviations must be nonnegative")
        candidates.append(parsed)
    return candidates


def build_qubo(
    candidates: list[dict],
    keff_min: float,
    keff_max: float,
    uncertainty_multiplier: float = 1.0,
    risk_weight: float = 1.0,
) -> dict:
    if not candidates:
        raise ValueError("no candidates supplied")
    if not (keff_min < keff_max):
        raise ValueError("require keff_min < keff_max")
    if uncertainty_multiplier < 0 or risk_weight < 0:
        raise ValueError("uncertainty_multiplier and risk_weight must be nonnegative")

    assessed = []
    for candidate in candidates:
        mean_k = candidate["mean_keff"]
        sd_k = candidate["between_seed_sd_keff"]
        lower = mean_k - uncertainty_multiplier * sd_k
        upper = mean_k + uncertainty_multiplier * sd_k
        score = (
            candidate["mean_fission_rate_peaking_factor"]
            + risk_weight * candidate["between_seed_sd_fission_peaking_factor"]
        )
        assessed.append({
            **candidate,
            "keff_seed_variability_lower": lower,
            "keff_seed_variability_upper": upper,
            "keff_band_feasible": lower >= keff_min and upper <= keff_max,
            "risk_adjusted_fission_peaking_score": score,
        })

    feasible = [row for row in assessed if row["keff_band_feasible"]]
    base = {
        "schema_version": "1.0",
        "formulation": "C5G7-specific one-hot selection QUBO; not legacy burnup-state QUBO",
        "status": "READY_FOR_EXTERNAL_QUBO_SOLVER" if feasible else "NO_FEASIBLE_CANDIDATE",
        "keff_acceptance_band": {"minimum": keff_min, "maximum": keff_max},
        "seed_variability_multiplier": uncertainty_multiplier,
        "risk_weight_for_fission_peaking_sd": risk_weight,
        "objective": "minimize mean_fission_peaking + risk_weight * between_seed_sd_fission_peaking",
        "feasibility_rule": "mean k_eff +/- uncertainty_multiplier * between-seed SD must lie fully inside the user-specified band",
        "uncertainty_interpretation": "descriptive seed-variability envelope, not a calibrated confidence interval",
        "candidate_count": len(assessed),
        "feasible_candidate_count": len(feasible),
        "candidate_assessments": assessed,
        "no_solver_run": True,
        "nonclaims": [
            "This does not map fresh/once_burned/twice_burned to UO2/MOX.",
            "This does not establish benchmark-grade convergence or physical safety.",
            "The fission-peaking objective is a relative fission-rate proxy, not absolute power.",
        ],
    }
    if not feasible:
        base["qubo_terms"] = []
        base["constant_offset"] = None
        base["penalties"] = None
        base["interpretation"] = "No candidate satisfies the specified k_eff band; do not run a solver or claim an optimum."
        return base

    scores = [row["risk_adjusted_fission_peaking_score"] for row in assessed]
    score_range = max(scores) - min(scores)
    one_hot_penalty = max(1.0, max(scores) + 1.0, score_range + 1.0)
    infeasible_penalty = max(1.0, score_range + 1.0)
    terms = []
    for i, row in enumerate(assessed):
        diagonal = row["risk_adjusted_fission_peaking_score"] - one_hot_penalty
        if not row["keff_band_feasible"]:
            diagonal += infeasible_penalty
        terms.append({"i": i, "j": i, "coefficient": diagonal})
    for i in range(len(assessed)):
        for j in range(i + 1, len(assessed)):
            terms.append({"i": i, "j": j, "coefficient": 2.0 * one_hot_penalty})
    base.update({
        "qubo_terms": terms,
        "variables": [{"index": i, "name": row["candidate_id"], "feasible": row["keff_band_feasible"]}
                      for i, row in enumerate(assessed)],
        "constant_offset": one_hot_penalty,
        "penalties": {"exactly_one_selected": one_hot_penalty, "selecting_infeasible_candidate": infeasible_penalty},
        "energy_convention": "E(x)=constant_offset + sum_i Q_ii*x_i + sum_{i<j} Q_ij*x_i*x_j",
        "interpretation": "The QUBO encodes one-hot selection and penalizes candidates whose descriptive k_eff seed-variability envelope falls outside the specified band. It is ready for a solver, but the result remains conditional on the supplied band and smoke-quality estimates.",
    })
    return base


def evaluate_energy(report: dict, bits: list[int]) -> float:
    if report.get("status") != "READY_FOR_EXTERNAL_QUBO_SOLVER":
        raise ValueError("QUBO is not selectable because no feasible candidate exists")
    if len(bits) != len(report["variables"]) or any(bit not in (0, 1) for bit in bits):
        raise ValueError("bit vector must contain one binary value per QUBO variable")
    energy = float(report["constant_offset"])
    for term in report["qubo_terms"]:
        energy += term["coefficient"] * bits[term["i"]] * bits[term["j"]]
    return energy


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-summary", required=True, type=Path)
    parser.add_argument("--keff-min", required=True, type=float)
    parser.add_argument("--keff-max", required=True, type=float)
    parser.add_argument("--uncertainty-multiplier", type=float, default=1.0)
    parser.add_argument("--risk-weight", type=float, default=1.0)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    if args.out.exists():
        parser.error(f"refusing to overwrite {args.out}")
    try:
        candidates = load_candidates(args.candidate_summary)
        report = build_qubo(candidates, args.keff_min, args.keff_max,
                            args.uncertainty_multiplier, args.risk_weight)
    except (OSError, ValueError, KeyError) as exc:
        parser.error(str(exc))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "candidate_count": report["candidate_count"],
                      "feasible_candidate_count": report["feasible_candidate_count"], "out": str(args.out)}, indent=2))
    return 0 if report["status"] == "READY_FOR_EXTERNAL_QUBO_SOLVER" else 2


if __name__ == "__main__":
    raise SystemExit(main())
