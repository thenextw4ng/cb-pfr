#!/usr/bin/env python3
"""Enumerate the six two-UO2/two-MOX layouts for the C5G7 2x2 fuel block.

This is a design-space generator, not a transport solver. It does not assign
burnup states, predict keff/power, or claim any candidate is physically better.
"""
from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path

POSITIONS = ("p00", "p01", "p10", "p11")
BASELINE = {"p00": "UO2", "p01": "MOX", "p10": "MOX", "p11": "UO2"}
REFLECTOR_POSITIONS = ("p02", "p12", "p20", "p21", "p22")


def build_design_space() -> dict:
    candidates = []
    for mox_positions in itertools.combinations(POSITIONS, 2):
        mox_set = set(mox_positions)
        layout = {
            position: ("MOX" if position in mox_set else "UO2")
            for position in POSITIONS
        }
        signature = "".join("M" if layout[p] == "MOX" else "U" for p in POSITIONS)
        candidates.append({
            "candidate_id": f"c5g7-2x2-{signature}",
            "layout_signature_order": list(POSITIONS),
            "fuel_assembly_layout": layout,
            "counts": {"UO2": 2, "MOX": 2},
            "is_canonical_reference_arrangement": layout == BASELINE,
            "requires_transport_evaluation": True,
            "physical_results": None,
        })

    return {
        "schema_version": "1.0",
        "design_study_id": "C5G7-2x2-two-UO2-two-MOX-layout-enumeration",
        "source_model": {
            "repository": "https://github.com/mit-crpg/benchmarks",
            "model_path": "c5g7/openmc/2d/build-xml-2d.py",
            "benchmark_specification": (
                "https://www.oecd-nea.org/jcms/pl_13548/"
                "benchmark-on-deterministic-transport-calculations-without-spatial-homogenisation"
            ),
        },
        "purpose": "Explicit reformulation of the design variables as C5G7 assembly-material placement.",
        "scope_boundary": (
            "This enumerates assembly-level permutations only. It is not a canonical C5G7 "
            "benchmark reproduction for non-reference arrangements and is not mapped to the "
            "legacy fresh/once_burned/twice_burned QUBO."
        ),
        "positions_order": list(POSITIONS),
        "fixed_reflector_positions": list(REFLECTOR_POSITIONS),
        "constraints": {
            "exactly_one_material_per_fuel_position": True,
            "exactly_two_UO2_assemblies": True,
            "exactly_two_MOX_assemblies": True,
            "reflector_positions_fixed": True,
        },
        "candidate_count": len(candidates),
        "canonical_reference_layout": BASELINE,
        "candidate_layouts": candidates,
        "optimization_protocol": {
            "objective": "To be predeclared after confirming the selected case's valid tallies and reference data.",
            "candidate_score": None,
            "required_simulator_outputs": [
                "effective multiplication factor with statistical uncertainty",
                "benchmark-compatible pin/assembly power or fission-rate tallies",
            ],
            "status": "design_space_defined_physics_not_yet_evaluated",
        },
        "nonclaims": [
            "No OpenMC run was performed by this script.",
            "No keff, neutron flux, or power result is predicted or fabricated.",
            "No candidate is ranked as physically superior.",
            "The canonical reference arrangement is a baseline identity check, not an optimization result.",
            "C5G7 UO2/MOX labels are not substitutes for burnup/depletion states.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, help="new JSON output path; existing files are not overwritten")
    args = parser.parse_args()
    output = Path(args.output).expanduser().resolve()
    if output.exists():
        parser.error(f"output already exists; refusing to overwrite: {output}")
    if not output.parent.is_dir():
        parser.error(f"parent directory does not exist: {output.parent}")
    output.write_text(json.dumps(build_design_space(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote {output}")
    print("Enumerated 6 layouts; no transport calculation or physical ranking was performed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
