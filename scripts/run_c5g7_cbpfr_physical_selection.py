#!/usr/bin/env python3
"""Run a fail-closed CB-PFR + one-hot QUBO selection audit on repeated C5G7 runs.

The input must be generated from actual corrected-group OpenMC statepoints. Bounds
and scales are caller-declared design criteria, not values inferred from the
canonical benchmark. This is not a mapping of the legacy burnup-state QUBO.
"""
from __future__ import annotations

import argparse
import csv
import itertools
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path

EXPECTED = {"MMUU", "MUMU", "MUUM", "UMMU", "UMUM", "UUMM"}
GROUP_EDGES = "1e-05;0.0635;10.0;100.0;1000.0;500000.0;1000000.0;20000000.0"
REQUIRED = {
    "round", "candidate_id", "layout_signature", "seed", "keff_mean",
    "keff_std_dev", "fission_rate_peaking_factor", "statepoint_sha256",
    "mgxs_sha256", "group_structure_audit", "mgxs_energy_group_boundaries_eV",
    "batches", "inactive", "particles_per_batch", "threads",
}


def _finite(row: dict, key: str, line: int) -> float:
    try:
        value = float(row[key])
    except (TypeError, ValueError) as exc:
        raise ValueError(f"line {line}: {key} must be numeric") from exc
    if not math.isfinite(value):
        raise ValueError(f"line {line}: {key} must be finite")
    return value


def load_and_validate(path: Path, *, min_batches: int, min_particles: int,
                      min_replicates: int) -> tuple[list[dict], dict]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        missing = REQUIRED - set(reader.fieldnames or ())
        if missing:
            raise ValueError(f"run-level CSV missing required columns: {sorted(missing)}")
        raw = list(reader)
    if not raw:
        raise ValueError("run-level CSV is empty")
    rows = []
    for line, row in enumerate(raw, start=2):
        sig = row["layout_signature"].strip()
        if sig not in EXPECTED or row["candidate_id"].strip() != f"c5g7-2x2-{sig}":
            raise ValueError(f"line {line}: candidate ID/signature is not one of the six declared layouts")
        if row["group_structure_audit"] != "PASS" or row["mgxs_energy_group_boundaries_eV"] != GROUP_EDGES:
            raise ValueError(f"line {line}: corrected standard C5G7 group structure audit failed")
        if not row["statepoint_sha256"].strip() or not row["mgxs_sha256"].strip():
            raise ValueError(f"line {line}: missing statepoint or MGXS SHA-256")
        item = {
            **row,
            "seed_i": int(row["seed"]),
            "batches_i": int(row["batches"]),
            "inactive_i": int(row["inactive"]),
            "particles_i": int(row["particles_per_batch"]),
            "threads_i": int(row["threads"]),
            "keff": _finite(row, "keff_mean", line),
            "keff_sd": _finite(row, "keff_std_dev", line),
            "fpeak": _finite(row, "fission_rate_peaking_factor", line),
        }
        if item["keff"] <= 0 or item["keff_sd"] <= 0 or item["fpeak"] <= 0:
            raise ValueError(f"line {line}: keff, its reported SD, and fission-peaking factor must be positive")
        if item["batches_i"] < min_batches or item["particles_i"] < min_particles:
            raise ValueError(f"line {line}: run budget is below requested minimum")
        if item["inactive_i"] < 0 or item["inactive_i"] >= item["batches_i"] or item["threads_i"] < 1:
            raise ValueError(f"line {line}: invalid run settings")
        rows.append(item)

    signatures = {r["layout_signature"] for r in rows}
    if signatures != EXPECTED:
        raise ValueError(f"expected all six layouts {sorted(EXPECTED)}, found {sorted(signatures)}")
    settings = {(r["batches_i"], r["inactive_i"], r["particles_i"], r["threads_i"]) for r in rows}
    if len(settings) != 1:
        raise ValueError("all candidates and repeats must use identical compute settings")
    hashes = [r["statepoint_sha256"] for r in rows]
    if len(hashes) != len(set(hashes)):
        raise ValueError("statepoint hashes must be unique across all runs")
    mgxs = {r["mgxs_sha256"] for r in rows}
    if len(mgxs) != 1:
        raise ValueError("all candidates and repeats must use the same MGXS hash")

    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        grouped[row["layout_signature"]].append(row)
    for sig, group in grouped.items():
        seeds = [r["seed_i"] for r in group]
        if len(group) < min_replicates or len(seeds) != len(set(seeds)):
            raise ValueError(f"{sig}: need at least {min_replicates} independent runs with unique seeds")
    return rows, {
        "run_count": len(rows),
        "layout_count": len(signatures),
        "common_settings": list(next(iter(settings))),
        "unique_statepoint_hashes": True,
        "single_mgxs_hash": next(iter(mgxs)),
        "standard_group_structure_audits_pass": True,
        "minimum_replicates_per_layout": min_replicates,
    }


def evaluate(rows: list[dict], *, keff_min: float, keff_max: float,
             fission_peaking_max: float, uncertainty_multiplier: float,
             keff_scale: float, fission_peaking_scale: float,
             risk_weight: float) -> dict:
    if not (0 < keff_min < keff_max):
        raise ValueError("require 0 < keff_min < keff_max")
    if fission_peaking_max <= 0 or uncertainty_multiplier < 0 or risk_weight < 0:
        raise ValueError("fission-peaking limit must be positive; multipliers/weights nonnegative")
    if keff_scale <= 0 or fission_peaking_scale <= 0:
        raise ValueError("violation scales must be positive")

    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        grouped[row["layout_signature"]].append(row)
    candidates = []
    for sig in sorted(EXPECTED):
        group = grouped[sig]
        ks = [r["keff"] for r in group]
        k_within = [r["keff_sd"] for r in group]
        fs = [r["fpeak"] for r in group]
        k_mean, f_mean = statistics.mean(ks), statistics.mean(fs)
        k_between = statistics.stdev(ks)
        f_between = statistics.stdev(fs)
        # Operational heuristic: use the larger of observed between-seed spread
        # and mean within-run k-eff SD; this is not a confidence interval.
        k_uncertainty = max(k_between, statistics.mean(k_within))
        f_uncertainty = f_between
        k_low = k_mean - uncertainty_multiplier * k_uncertainty
        k_high = k_mean + uncertainty_multiplier * k_uncertainty
        f_high = f_mean + uncertainty_multiplier * f_uncertainty
        violations = (
            max(0.0, keff_min - k_low) + max(0.0, k_high - keff_max),
            max(0.0, f_high - fission_peaking_max),
        )
        normalized_violation = violations[0] / keff_scale + violations[1] / fission_peaking_scale
        feasible = k_low >= keff_min and k_high <= keff_max and f_high <= fission_peaking_max
        candidates.append({
            "candidate_id": f"c5g7-2x2-{sig}",
            "layout_signature": sig,
            "replicate_count": len(group),
            "seeds": sorted(r["seed_i"] for r in group),
            "mean_keff": k_mean,
            "between_seed_sd_keff": k_between,
            "mean_within_run_keff_sd": statistics.mean(k_within),
            "operational_keff_uncertainty": k_uncertainty,
            "keff_bound": [k_low, k_high],
            "mean_fission_rate_peaking_factor": f_mean,
            "between_seed_sd_fission_peaking_factor": f_uncertainty,
            "fission_peaking_upper_bound": f_high,
            "normalized_conservative_violation": normalized_violation,
            "conservatively_feasible": feasible,
            "uncertainty_interpretation": "operational heuristic, not a calibrated confidence interval",
        })

    feasible = [c for c in candidates if c["conservatively_feasible"]]
    if not feasible:
        return {
            "schema_version": "1.0",
            "status": "NO_CONSERVATIVELY_FEASIBLE_CANDIDATE",
            "winner_selected": False,
            "limits": {"keff": [keff_min, keff_max], "fission_peaking_max": fission_peaking_max,
                       "uncertainty_multiplier": uncertainty_multiplier, "risk_weight": risk_weight,
                       "keff_violation_scale": keff_scale, "fission_peaking_violation_scale": fission_peaking_scale},
            "candidates": candidates,
            "qubo": None,
            "interpretation": "No candidate passes the caller-declared conservative screen; no QUBO winner is emitted.",
        }

    scores = {c["candidate_id"]: c["mean_fission_rate_peaking_factor"] +
              risk_weight * c["between_seed_sd_fission_peaking_factor"] for c in candidates}
    lo, hi = min(scores.values()), max(scores.values())
    normalized = {cid: ((value - lo) / (hi - lo) if hi > lo else 0.0) for cid, value in scores.items()}
    ids = [f"c5g7-2x2-{sig}" for sig in sorted(EXPECTED)]
    feasible_ids = {c["candidate_id"] for c in feasible}
    one_hot_penalty, infeasible_penalty = 2.0, 2.0
    diagonal = [normalized[cid] + (0.0 if cid in feasible_ids else infeasible_penalty) - one_hot_penalty for cid in ids]
    q = [[0.0 for _ in ids] for _ in ids]
    for i, value in enumerate(diagonal):
        q[i][i] = value
        for j in range(i + 1, len(ids)):
            q[i][j] = 2.0 * one_hot_penalty
    offset = one_hot_penalty

    # Exhaustive minimization is exact for six binary selector variables.
    states = []
    for bits in itertools.product((0, 1), repeat=len(ids)):
        energy = offset + sum(q[i][i] * bits[i] for i in range(len(ids))) + sum(
            q[i][j] * bits[i] * bits[j] for i in range(len(ids)) for j in range(i + 1, len(ids))
        )
        states.append((energy, bits))
    best_energy = min(e for e, _ in states)
    minimizers = [bits for e, bits in states if math.isclose(e, best_energy, abs_tol=1e-10)]
    if len(minimizers) != 1 or sum(minimizers[0]) != 1:
        raise RuntimeError("QUBO failed exact one-hot uniqueness/feasibility check")
    chosen_id = ids[minimizers[0].index(1)]
    cbpfr_winner = min(feasible, key=lambda c: (c["normalized_conservative_violation"], scores[c["candidate_id"]], c["candidate_id"]))["candidate_id"]
    if chosen_id != cbpfr_winner:
        raise RuntimeError(f"QUBO winner {chosen_id} does not match CB-PFR winner {cbpfr_winner}")

    return {
        "schema_version": "1.0",
        "status": "SELECTION_PIPELINE_PASS_PHYSICAL_VALIDATION_NOT_CERTIFIED",
        "winner_selected": True,
        "selected_candidate_id": chosen_id,
        "cbpfr_selected_candidate_id": cbpfr_winner,
        "qubo_energy": best_energy,
        "limits": {"keff": [keff_min, keff_max], "fission_peaking_max": fission_peaking_max,
                   "uncertainty_multiplier": uncertainty_multiplier, "risk_weight": risk_weight,
                   "keff_violation_scale": keff_scale, "fission_peaking_violation_scale": fission_peaking_scale},
        "candidate_count": len(candidates),
        "feasible_candidate_count": len(feasible),
        "candidates": candidates,
        "qubo": {"variable_order": ids, "matrix_upper_triangular": q, "offset": offset,
                 "one_hot_penalty": one_hot_penalty, "infeasible_candidate_penalty": infeasible_penalty,
                 "exact_binary_states_enumerated": len(states), "unique_one_hot_minimizer": True},
        "interpretation": (
            "The pipeline proves consistency between the declared CB-PFR screen and its one-hot selector "
            "for this supplied OpenMC dataset. It does not certify the model as an official benchmark, "
            "prove safety, or validate the separate legacy fresh/once_burned/twice_burned QUBO mapping."
        ),
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--run-level-csv", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--keff-min", type=float, required=True)
    p.add_argument("--keff-max", type=float, required=True)
    p.add_argument("--fission-peaking-max", type=float, required=True)
    p.add_argument("--uncertainty-multiplier", type=float, required=True)
    p.add_argument("--keff-scale", type=float, required=True)
    p.add_argument("--fission-peaking-scale", type=float, required=True)
    p.add_argument("--risk-weight", type=float, required=True)
    p.add_argument("--min-batches", type=int, required=True)
    p.add_argument("--min-particles", type=int, required=True)
    p.add_argument("--min-replicates", type=int, default=3)
    args = p.parse_args()
    if args.out.exists():
        p.error(f"refusing to overwrite existing output: {args.out}")
    try:
        rows, evidence = load_and_validate(args.run_level_csv, min_batches=args.min_batches,
                                           min_particles=args.min_particles, min_replicates=args.min_replicates)
        report = evaluate(rows, keff_min=args.keff_min, keff_max=args.keff_max,
                          fission_peaking_max=args.fission_peaking_max,
                          uncertainty_multiplier=args.uncertainty_multiplier,
                          keff_scale=args.keff_scale, fission_peaking_scale=args.fission_peaking_scale,
                          risk_weight=args.risk_weight)
        report["evidence_audit"] = evidence
        report["input_csv"] = str(args.run_level_csv)
    except (OSError, ValueError, RuntimeError) as exc:
        p.error(str(exc))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "winner_selected": report["winner_selected"],
                      "selected_candidate_id": report.get("selected_candidate_id")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
