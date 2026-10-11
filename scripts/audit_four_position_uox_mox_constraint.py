#!/usr/bin/env python3
"""Exhaustive combinatorial check for the separate four-position UO2/MOX study.

This validates only the exactly-two-MOX/two-UO2 constraint and position-label
permutations. It does not validate OpenMC material definitions or reactor physics.
"""
from __future__ import annotations
import itertools
import json
from pathlib import Path

POSITIONS = ("P1", "P2", "P3", "P4")

def enumerate_feasible() -> list[dict[str, str]]:
    rows = []
    for values in itertools.product(("U", "M"), repeat=4):
        if values.count("M") == 2 and values.count("U") == 2:
            rows.append(dict(zip(POSITIONS, values)))
    return rows

def audit() -> dict:
    all_assignments = list(itertools.product(("U", "M"), repeat=4))
    feasible = enumerate_feasible()
    signatures = ["".join(row[p] for p in POSITIONS) for row in feasible]
    return {
        "schema_version": "1.0",
        "scope": "combinatorial_constraint_only",
        "total_binary_assignments": len(all_assignments),
        "feasible_assignments": len(feasible),
        "expected_feasible_assignments": 6,
        "all_feasible_have_two_U_and_two_M": all(
            list(row.values()).count("U") == 2 and list(row.values()).count("M") == 2
            for row in feasible
        ),
        "unique_signatures": len(set(signatures)) == 6,
        "position_order": list(POSITIONS),
        "feasible_signatures": signatures,
        "physical_mapping_validated": False,
        "interpretation": "Passing proves the binary count constraint only; material provenance, geometry, transport, convergence and independent review are separate gates."
    }

def main() -> int:
    result = audit()
    print(json.dumps(result, indent=2))
    if result["total_binary_assignments"] != 16 or result["feasible_assignments"] != 6:
        return 1
    if not result["all_feasible_have_two_U_and_two_M"] or not result["unique_signatures"]:
        return 1
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
