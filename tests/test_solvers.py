"""Tests for the solver layer; no QPU credentials or OpenMC are required."""
import unittest

from cbpfr.qubo import CoreSpec, build_usmanov_style_qubo
from cbpfr.solvers import (
    SolverContractError,
    candidates_from_solver_run,
    model_to_upper_triangular_qubo,
    solve_exact,
)


class SolverLayerTests(unittest.TestCase):
    def setUp(self):
        spec = CoreSpec(
            name="solver-fixture",
            positions=("A", "B"),
            boundary=frozenset(),
            inner=frozenset(),
            edges=(),
            inventory=(1, 1, 0),
            description="Tiny test fixture, not reactor geometry.",
        )
        self.model = build_usmanov_style_qubo(spec)

    def test_exact_solver_returns_feasible_solutions_and_truthful_class(self):
        result = solve_exact(self.model, max_variables=6, max_solutions=3)
        self.assertEqual(result.solver_class, "classical_exact")
        self.assertFalse(result.metadata["is_quantum_hardware"])
        self.assertFalse(result.metadata["quantum_advantage_established"])
        self.assertTrue(result.solutions)
        self.assertTrue(all(row.feasible for row in result.solutions))
        self.assertEqual(len(candidates_from_solver_run(result)), len(result.solutions))

    def test_exact_solver_refuses_large_models_by_default(self):
        with self.assertRaisesRegex(SolverContractError, "exact enumeration blocked"):
            solve_exact(self.model, max_variables=2)

    def test_qubo_conversion_preserves_offset_separately(self):
        q, offset = model_to_upper_triangular_qubo(self.model)
        self.assertTrue(q)
        self.assertEqual(offset, self.model.offset)
        vector = (1, 0, 0, 0, 1, 0)
        energy_from_dict = offset + sum(value * vector[i] * vector[j] for (i, j), value in q.items())
        self.assertAlmostEqual(energy_from_dict, self.model.energy(vector))

    def test_invalid_solver_metadata_rejected(self):
        with self.assertRaisesRegex(SolverContractError, "solver_class"):
            from cbpfr.solvers import _validate_run_args
            _validate_run_args("made up", "quantumish", 10)

    def test_candidates_can_include_infeasible_solutions_only_by_opt_in(self):
        result = solve_exact(self.model, max_variables=6, max_solutions=6)
        candidates = candidates_from_solver_run(result, feasible_only=False)
        self.assertEqual(len(candidates), len(result.solutions))


if __name__ == "__main__":
    unittest.main()
