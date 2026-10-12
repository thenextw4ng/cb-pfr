"""Exhaustive algebraic regression tests for the categorical QUBO expansion."""
from __future__ import annotations

import itertools
import math
import unittest

from cbpfr.qubo import (
    CandidateMappingError,
    CoreSpec,
    ModelSpecificationError,
    build_usmanov_style_qubo,
    categorical_vector,
    enumerate_feasible_candidates,
)


class QuboAlgebraicRegressionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.spec = CoreSpec(
            name="four-position-regression",
            positions=("A", "B", "C", "D"),
            boundary=frozenset(("A", "D")),
            inner=frozenset(("B", "C")),
            edges=(("A", "B"), ("B", "C"), ("C", "D")),
            inventory=(1, 2, 1),
            symmetry_pairs=(("A", "D"),),
            description="Small deterministic algebraic regression fixture.",
        )
        self.model = build_usmanov_style_qubo(self.spec)

    def test_energy_matches_direct_penalty_expansion_exhaustively(self) -> None:
        for categories in itertools.product(range(3), repeat=len(self.spec.positions)):
            vector = categorical_vector(self.spec, categories)
            direct = sum(self.model.direct_penalty_terms(vector).values())
            self.assertTrue(math.isclose(self.model.energy(vector), direct, rel_tol=0.0, abs_tol=1e-10),
                            msg=f"energy mismatch for {categories}")

    def test_enumerated_candidates_are_feasible_and_unique(self) -> None:
        candidates = enumerate_feasible_candidates(self.model)
        vectors = [candidate.vector for candidate in candidates]
        self.assertTrue(vectors)
        self.assertEqual(len(vectors), len(set(vectors)))
        for vector in vectors:
            self.assertTrue(self.model.is_feasible(vector))
            self.assertAlmostEqual(self.model.energy(vector), 0.0, delta=1e-10)

    def test_categorical_encoding_is_one_hot_per_position(self) -> None:
        n = len(self.spec.positions)
        for categories in itertools.product(range(3), repeat=n):
            vector = categorical_vector(self.spec, categories)
            for position_index in range(n):
                self.assertEqual(sum(vector[burnup * n + position_index] for burnup in range(3)), 1)

    def test_invalid_categorical_inputs_are_rejected(self) -> None:
        for bad in ((0, 1, 2), (0, 1, 2, 3), (0, 1, -1, 2)):
            with self.subTest(categories=bad):
                with self.assertRaises(CandidateMappingError):
                    categorical_vector(self.spec, bad)

    def test_core_spec_rejects_duplicate_positions(self) -> None:
        with self.assertRaises(ModelSpecificationError):
            CoreSpec(name="invalid", positions=("A", "A"), boundary=frozenset(),
                     inner=frozenset(), edges=(), inventory=(1, 1, 0))

    def test_qubo_rejects_wrong_length_and_nonbinary_vectors(self) -> None:
        with self.assertRaises(CandidateMappingError):
            self.model.energy([0] * (self.model.variable_count - 1))
        invalid = [0] * self.model.variable_count
        invalid[0] = 0.5
        with self.assertRaises(CandidateMappingError):
            self.model.energy(invalid)


if __name__ == "__main__":
    unittest.main()
