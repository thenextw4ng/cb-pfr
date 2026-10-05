import unittest

from cbpfr.qubo import CoreSpec, build_usmanov_style_qubo, enumerate_feasible_candidates
from cbpfr.ranking import MetricLimit, PhysicalEstimate, rank_all_methods, selected_is_conservatively_feasible


class CBPFRSmokeTests(unittest.TestCase):
    def setUp(self):
        self.spec = CoreSpec(
            name="seven_position_toy",
            positions=tuple(f"p{i}" for i in range(7)),
            boundary=frozenset({"p0", "p1", "p2", "p3", "p4", "p5"}),
            inner=frozenset({"p6"}),
            edges=tuple((f"p{i}", f"p{(i + 1) % 6}") for i in range(6)),
            inventory=(3, 3, 1),
        )
        self.model = build_usmanov_style_qubo(self.spec)

    def test_exact_qpu_energy_matches_direct_penalty(self):
        candidate = enumerate_feasible_candidates(self.model)[0]
        self.assertAlmostEqual(
            self.model.energy(candidate.vector),
            sum(self.model.direct_penalty_terms(candidate.vector).values()),
        )

    def test_conservative_ranking_selects_screened_candidate(self):
        candidates = enumerate_feasible_candidates(self.model)[:3]
        metric = MetricLimit(name="response", upper=1.0, z=1.0, scale=1.0, uncertainty_kind="known_se")
        estimates = {
            c.candidate_id: PhysicalEstimate(c.candidate_id, {"response": (0.9, 0.01)})
            for c in candidates
        }
        result = rank_all_methods(self.model, candidates, estimates, [metric], {"response": 0.0})
        self.assertIn(result["cb_pfr"][0].method, {"cb_pfr", "point_estimate", "uniform_margin"})
        self.assertTrue(selected_is_conservatively_feasible(result["cb_pfr"][0]))

    def test_invalid_uncertainty_fails_closed(self):
        candidate = enumerate_feasible_candidates(self.model)[0]
        metric = MetricLimit(name="response", upper=1.0, z=1.0, uncertainty_kind="unknown")
        estimate = PhysicalEstimate(candidate.candidate_id, {"response": (0.5, -1.0)})
        result = rank_all_methods(self.model, [candidate], {candidate.candidate_id: estimate}, [metric], {"response": 0.0})
        self.assertEqual(result["cb_pfr"][0].physical.indicator, 1)
        self.assertEqual(result["cb_pfr"][0].physical.metric_assessments[0].status, "nonfinite_or_negative")


if __name__ == "__main__":
    unittest.main()
