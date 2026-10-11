"""Exact QUBO encoding for the separate four-position C5G7 UO2/MOX design study.

This is deliberately NOT a mapping of the legacy fresh/once_burned/twice_burned
QUBO. It encodes four assembly-material decisions with exactly two MOX
assemblies. The OpenMC transport score remains an external simulator result.
"""
from __future__ import annotations

from itertools import combinations
from typing import Sequence

POSITIONS = ("p00", "p01", "p10", "p11")


class C5G7DesignError(ValueError):
    """Invalid vector or assembly assignment."""


def qubo_energy(vector: Sequence[int], penalty: float = 1.0) -> float:
    """Evaluate A(sum(y)-2)^2 using y_i=1 for MOX and y_i=0 for UO2."""
    y = tuple(vector)
    if len(y) != len(POSITIONS):
        raise C5G7DesignError(f"expected {len(POSITIONS)} binary variables")
    if any(isinstance(v, bool) is False and v not in (0, 1) for v in y):
        raise C5G7DesignError("each material variable must be 0 (UO2) or 1 (MOX)")
    if penalty <= 0:
        raise C5G7DesignError("penalty must be positive")
    return float(penalty * (sum(y) - 2) ** 2)


def assignment_from_vector(vector: Sequence[int]) -> dict[str, str]:
    """Decode an assignment; rejects infeasible material counts."""
    y = tuple(vector)
    qubo_energy(y)  # validates length and binary values
    if sum(y) != 2:
        raise C5G7DesignError("assignment must contain exactly two MOX and two UO2 assemblies")
    return {position: ("MOX" if y[i] else "UO2") for i, position in enumerate(POSITIONS)}


def vector_from_assignment(assignment: dict[str, str]) -> tuple[int, ...]:
    if set(assignment) != set(POSITIONS):
        raise C5G7DesignError(f"assignment positions must be exactly {POSITIONS}")
    if any(value not in ("UO2", "MOX") for value in assignment.values()):
        raise C5G7DesignError("material labels must be UO2 or MOX")
    vector = tuple(int(assignment[position] == "MOX") for position in POSITIONS)
    qubo_energy(vector)
    if sum(vector) != 2:
        raise C5G7DesignError("assignment must contain exactly two MOX and two UO2 assemblies")
    return vector


def enumerate_feasible_assignments() -> list[dict[str, str]]:
    """Return the six exact-cardinality layouts in stable position order."""
    results = []
    for mox_indices in combinations(range(len(POSITIONS)), 2):
        selected = set(mox_indices)
        results.append({
            position: ("MOX" if i in selected else "UO2")
            for i, position in enumerate(POSITIONS)
        })
    return results


def upper_triangular_qubo(penalty: float = 1.0) -> tuple[tuple[float, ...], ...]:
    """Return Q for E(y)=offset + sum_i Qii*y_i + sum_{i<j} Qij*y_i*y_j.

    Expansion: A(sum(y)-2)^2 = 4A - 3A*sum(y) + 2A*sum_{i<j}(y_i*y_j).
    The returned matrix stores only the upper triangle; the constant 4A is
    returned separately.
    """
    if penalty <= 0:
        raise C5G7DesignError("penalty must be positive")
    q = [[0.0] * len(POSITIONS) for _ in POSITIONS]
    for i in range(len(POSITIONS)):
        q[i][i] = -3.0 * penalty
        for j in range(i + 1, len(POSITIONS)):
            q[i][j] = 2.0 * penalty
    return tuple(tuple(row) for row in q)
