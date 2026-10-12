"""Property-style regression tests for the exact categorical QUBO expansion.

These tests verify algebraic equivalence and hard invariants without invoking
OpenMC or requiring external nuclear-data files.
"""
from __future__ import annotations

import itertools
import math

import pytest

from cbpfr.qubo import (
    CandidateMappingError,
    CoreSpec,
    ModelSpecificationError,
    build_usmanov_style_qubo,
    categorical_vector,
    enumerate_feasible_candidates,
)


@pytest.fixture
def small_spec() -> CoreSpec:
    return CoreSpec(
        name="four-position-regression",
        positions=("A", "B", "C", "D"),
        boundary=frozenset(("A", "D")),
        inner=frozenset(("B", "C")),
        edges=(("A", "B"), ("B", "C"), ("C", "D")),
        inventory=(1, 2, 1),
        symmetry_pairs=(("A", "D"),),
        description="Small deterministic algebraic regression fixture.",
    )


def test_qubo_energy_matches_direct_penalty_expansion(small_spec: CoreSpec) -> None:
    model = build_usmanov_style_qubo(small_spec)
    for categories in itertools.product(range(3), repeat=len(small_spec.positions)):
        vector = categorical_vector(small_spec, categories)
        direct = sum(model.direct_penalty_terms(vector).values())
        assert math.isclose(model.energy(vector), direct, rel_tol=0.0, abs_tol=1e-10)


def test_every_enumerated_candidate_is_feasible_and_unique(small_spec: CoreSpec) -> None:
    model = build_usmanov_style_qubo(small_spec)
    candidates = enumerate_feasible_candidates(model)
    vectors = [candidate.vector for candidate in candidates]
    assert vectors
    assert len(vectors) == len(set(vectors))
    assert all(model.is_feasible(vector) for vector in vectors)
    assert all(model.energy(vector) == pytest.approx(0.0, abs=1e-10) for vector in vectors)


def test_categorical_encoding_is_one_hot_per_position(small_spec: CoreSpec) -> None:
    for categories in itertools.product(range(3), repeat=len(small_spec.positions)):
        vector = categorical_vector(small_spec, categories)
        n = len(small_spec.positions)
        for position_index in range(n):
            assert sum(vector[burnup * n + position_index] for burnup in range(3)) == 1


@pytest.mark.parametrize("bad_categories", [
    (0, 1, 2),       # wrong length
    (0, 1, 2, 3),     # invalid category
    (0, 1, -1, 2),    # invalid category
])
def test_categorical_encoder_rejects_invalid_input(
    small_spec: CoreSpec, bad_categories: tuple[int, ...]
) -> None:
    with pytest.raises(CandidateMappingError):
        categorical_vector(small_spec, bad_categories)


def test_core_spec_rejects_duplicate_positions() -> None:
    with pytest.raises(ModelSpecificationError):
        CoreSpec(
            name="invalid",
            positions=("A", "A"),
            boundary=frozenset(),
            inner=frozenset(),
            edges=(),
            inventory=(1, 1, 0),
        )


def test_qubo_rejects_nonbinary_vectors(small_spec: CoreSpec) -> None:
    model = build_usmanov_style_qubo(small_spec)
    with pytest.raises(CandidateMappingError):
        model.energy([0] * (model.variable_count - 1))
    invalid = [0] * model.variable_count
    invalid[0] = 0.5  # type: ignore[list-item]
    with pytest.raises(CandidateMappingError):
        model.energy(invalid)
