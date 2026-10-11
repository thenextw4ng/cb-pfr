#!/usr/bin/env python3
"""Create a fail-closed, metric-aware comparison with the single published C5G7 baseline.

Only k-effective is compared in the current CSV because the publication's 2.498
quantity is maximum *pin power*, whereas the local analysis produces an
assembly-integrated fission-rate peaking factor. Similar numeric names do not
make those observables interchangeable.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path


FIELDS = [
    "candidate_id", "metric", "simulation_value", "simulation_standard_uncertainty",
    "reference_value", "reference_standard_uncertainty", "absolute_difference",
    "relative_difference_percent", "combined_standard_uncertainty_independent",
    "difference_over_combined_uncertainty", "comparison_status", "notes",
]


def compare(simulation: dict, reference: dict) -> list[dict[str, str]]:
    candidate_id = simulation.get("candidate_id")
    if not candidate_id or candidate_id != reference.get("candidate_id"):
        raise ValueError("simulation and reference candidate_id must match exactly")
    rows: list[dict[str, str]] = []

    sim = float(simulation["keff_mean"])
    sim_u = float(simulation["keff_std_dev"])
    ref = float(reference["keff_mean"])
    ref_u = float(reference["keff_uncertainty"])
    if not all(math.isfinite(x) for x in (sim, sim_u, ref, ref_u)) or min(sim_u, ref_u) < 0 or ref == 0:
        raise ValueError("keff values and uncertainties must be finite, uncertainty nonnegative, reference nonzero")
    delta = sim - ref
    combined = math.hypot(sim_u, ref_u)
    rows.append({
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
        "comparison_status": "NUMERICAL_SCREEN_ONLY_MODEL_IDENTITY_BLOCKED_LOW_STAT",
        "notes": (
            "The observables are both k_eff for the nominal canonical arrangement, but this run has "
            "only 15 active batches x 100 particles and large reported Monte Carlo uncertainty. "
            "Model/material/boundary-condition identity has not passed independent primary-specification "
            "review. Combined uncertainty assumes independent estimates; this is not an acceptance test."
        ),
    })

    rows.append({
        "candidate_id": candidate_id,
        "metric": "assembly_integrated_fission_rate_peaking_factor",
        "simulation_value": f"{float(simulation['fission_rate_peaking_factor']):.12g}",
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
            "maximum normalized pin power, not this code's max assembly-integrated fission-rate / mean "
            "assembly-integrated fission-rate. No numeric comparison is made. Reference: Song et al. "
            "(2020), Table 1, https://doi.org/10.3389/fenrg.2020.00124."
        ),
    })
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--simulation-json", required=True, type=Path)
    parser.add_argument("--reference-csv", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    if args.out.exists():
        parser.error(f"refusing to overwrite existing output: {args.out}")
    try:
        simulation = json.loads(args.simulation_json.read_text(encoding="utf-8"))
        with args.reference_csv.open(newline="", encoding="utf-8") as handle:
            references = list(csv.DictReader(handle))
        candidate_id = simulation.get("candidate_id")
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
