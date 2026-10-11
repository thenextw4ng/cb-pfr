#!/usr/bin/env python3
"""Create a fail-closed, metric-aware comparison with the published C5G7 baseline.

Accepts either one per-statepoint analysis JSON or the committed aggregate summary
from a multi-seed smoke run. The publication's 2.498 quantity is maximum pin
power, whereas this repository computes assembly-integrated fission peaking;
those observables are deliberately not compared.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any


FIELDS = [
    "candidate_id", "metric", "simulation_value", "simulation_standard_uncertainty",
    "reference_value", "reference_standard_uncertainty", "absolute_difference",
    "relative_difference_percent", "combined_standard_uncertainty_independent",
    "difference_over_combined_uncertainty", "comparison_status", "notes",
]


def _normalise_simulation(simulation: dict[str, Any], candidate_id: str) -> dict[str, Any]:
    """Normalize a single-run report or an aggregate summary to a common schema."""
    if isinstance(simulation.get("candidates"), list):
        matches = [x for x in simulation["candidates"] if x.get("candidate_id") == candidate_id]
        if len(matches) != 1:
            raise ValueError(f"expected exactly one aggregate candidate {candidate_id}, got {len(matches)}")
        item = matches[0]
        n_runs = item.get("n_runs")
        sd = float(item["between_seed_sd_keff"])
        if isinstance(n_runs, bool) or not isinstance(n_runs, int) or n_runs < 2:
            raise ValueError("aggregate candidate must declare n_runs >= 2")
        return {
            "candidate_id": candidate_id,
            "keff_mean": float(item["mean_keff"]),
            "keff_std_dev": sd / math.sqrt(n_runs),
            "fission_rate_peaking_factor": float(item["mean_fission_rate_peaking_factor"]),
            "uncertainty_kind": "between_seed_standard_error_of_mean",
            "n_runs": n_runs,
            "settings": simulation.get("settings", {}),
            "workflow_run_id": simulation.get("workflow_run_id"),
        }
    if simulation.get("candidate_id") != candidate_id:
        raise ValueError("simulation and reference candidate_id must match exactly")
    return {
        **simulation,
        "uncertainty_kind": "within_run_reported_standard_uncertainty",
        "n_runs": 1,
        "settings": {
            "batches": simulation.get("n_batches"),
            "inactive_batches": simulation.get("n_inactive"),
            "particles_per_batch": simulation.get("n_particles"),
        },
    }


def compare(simulation: dict[str, Any], reference: dict[str, Any]) -> list[dict[str, str]]:
    candidate_id = reference.get("candidate_id")
    if not candidate_id:
        raise ValueError("reference candidate_id is required")
    simdata = _normalise_simulation(simulation, candidate_id)

    sim = float(simdata["keff_mean"])
    sim_u = float(simdata["keff_std_dev"])
    ref = float(reference["keff_mean"])
    ref_u = float(reference["keff_uncertainty"])
    if not all(math.isfinite(x) for x in (sim, sim_u, ref, ref_u)) or min(sim_u, ref_u) < 0 or ref == 0:
        raise ValueError("keff values and uncertainties must be finite, uncertainty nonnegative, reference nonzero")
    delta = sim - ref
    combined = math.hypot(sim_u, ref_u)
    n_runs = int(simdata.get("n_runs", 1))
    if n_runs > 1:
        status = "NUMERICAL_SCREEN_ONLY_MODEL_IDENTITY_BLOCKED_SMOKE_BUDGET"
        settings = simdata.get("settings", {})
        note = (
            f"Mean of {n_runs} independent seed runs; simulation uncertainty is the between-seed "
            f"standard error of the mean (sample SD/sqrt(n)); settings={settings}. "
            "Combined uncertainty assumes independent simulation/reference estimates. Model identity "
            "review remains blocked; this is not an acceptance test."
        )
    else:
        status = "NUMERICAL_SCREEN_ONLY_MODEL_IDENTITY_BLOCKED_LOW_STAT"
        settings = simdata.get("settings", {})
        note = (
            f"Single-run settings={settings}; simulation uncertainty is the within-run reported "
            "standard uncertainty. Combined uncertainty assumes independent estimates. Model identity "
            "review remains blocked; this is not an acceptance test."
        )
    if simdata.get("workflow_run_id") is not None:
        note += f" Workflow run: {simdata['workflow_run_id']}."

    rows = [{
        "candidate_id": candidate_id,
        "metric": "k_eff",
        "simulation_value": f"{sim:.12g}",
        "simulation_standard_uncertainty": f"{sim_u:.12g}",
        "reference_value": f"{ref:.12g}",
        "reference_standard_uncertainty": f"{ref_u:.12g}",
        "absolute_difference": f"{delta:.12g}",
        "relative_difference_percent": f"{100.0 * delta / ref:.8g}",
        "combined_standard_uncertainty_independent": f"{combined:.12g}",
        "difference_over_combined_uncertainty": f"{delta / combined:.8g}" if combined > 0 else "",
        "comparison_status": status,
        "notes": note,
    }]

    pf = float(simdata.get("fission_rate_peaking_factor", math.nan))
    if not math.isfinite(pf):
        raise ValueError("simulation must contain a finite assembly fission-rate peaking factor")
    rows.append({
        "candidate_id": candidate_id,
        "metric": "assembly_integrated_fission_rate_peaking_factor",
        "simulation_value": f"{pf:.12g}",
        "simulation_standard_uncertainty": "",
        "reference_value": "",
        "reference_standard_uncertainty": "",
        "absolute_difference": "",
        "relative_difference_percent": "",
        "combined_standard_uncertainty_independent": "",
        "difference_over_combined_uncertainty": "",
        "comparison_status": "BLOCKED_NOT_COMPARABLE_OBSERVABLE",
        "notes": (
            "Published CSV legacy field fission_rate_peaking_factor=2.498 is actually the publication's "
            "maximum normalized pin power, not this code's assembly-integrated fission-rate ratio. "
            "No numeric comparison is made. Reference: Song et al. (2020), Table 1, "
            "https://doi.org/10.3389/fenrg.2020.00124."
        ),
    })
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--simulation-json", required=True, type=Path,
                        help="per-statepoint analysis JSON or a multi-seed aggregate summary JSON")
    parser.add_argument("--reference-csv", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    if args.out.exists():
        parser.error(f"refusing to overwrite existing output: {args.out}")
    try:
        simulation = json.loads(args.simulation_json.read_text(encoding="utf-8"))
        with args.reference_csv.open(newline="", encoding="utf-8") as handle:
            references = list(csv.DictReader(handle))
        if "candidate_id" in simulation:
            candidate_id = simulation["candidate_id"]
        elif isinstance(simulation.get("candidates"), list):
            ids = [row.get("candidate_id") for row in references]
            candidate_id = next((x for x in ids if any(c.get("candidate_id") == x for c in simulation["candidates"])), None)
        else:
            candidate_id = None
        matches = [row for row in references if row.get("candidate_id") == candidate_id]
        if len(matches) != 1:
            raise ValueError(f"expected exactly one reference row for {candidate_id}, got {len(matches)}")
        rows = compare(simulation, matches[0])
    except (OSError, json.JSONDecodeError, csv.Error, KeyError, TypeError, ValueError) as exc:
        parser.error(str(exc))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps({"status": "COMPARISON_RECORDED_WITH_GATES", "rows": len(rows),
                      "out": str(args.out)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
