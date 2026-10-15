"""Portable regression tests for the anonymous CB-PFR supplement.

Run from the repository root with:
    PYTHONPATH=paper/submission/supplementary python -m unittest discover \
        -s paper/submission/supplementary/tests -v

These tests establish software properties only. They do not validate OpenMC
physics, benchmark accuracy, or reactor-engineering acceptance limits.
"""
from __future__ import annotations

import math
import unittest

from cbpfr.qubo import CoreSpec, build_usmanov_style_qubo, enumerate_feasible_candidates
from cbpfr.ranking import (
    MetricLimit,
    PhysicalEstimate,
    assess_physical,
    rank_all_methods,
    selected_is_conservatively_feasible,
)


class CBPFRFormalPropertyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.spec = CoreSpec(
            name="formal-property-test",
            positions=("p0", "p1", "p2"),
            boundary=frozenset(),
            inner=frozenset(),
            edges=(),
            inventory=(1, 1, 1),
        )
        self.model = build_usmanov_style_qubo(self.spec)
        self.candidates = enumerate_feasible_candidates(self.model)
        self.metric = MetricLimit(
            name="response", upper=1.0, z=1.0, scale=0.1, weight=1.0,
            uncertainty_kind="test_between_run_sd", units="arbitrary",
        )

    def _estimates(self, values=None):
        values = values or [
            (0.4, 0.02), (0.95, 0.04), (1.05, 0.02),
            (1.2, 0.02), (0.6, 0.01), (0.8, 0.03),
        ]
        return {
            candidate.candidate_id: PhysicalEstimate(
                candidate.candidate_id, {"response": value}
            )
            for candidate, value in zip(self.candidates, values)
        }

    def test_1_violation_nondecreasing_and_pass_set_nested_as_z_increases(self):
        means = [0.70, 0.90, 0.96, 1.00, 1.04, 1.20]
        estimates = self._estimates([(mean, 0.03) for mean in means])
        passes_by_z = []
        violations_by_candidate = {c.candidate_id: [] for c in self.candidates}
        for z in (0.0, 1.0, 2.0):
            metric = MetricLimit(
                name="response", upper=1.0, z=z, scale=1.0, weight=1.0,
                uncertainty_kind="test_se", units="arbitrary",
            )
            ranks = rank_all_methods(
                self.model, self.candidates, estimates, [metric], {"response": 0.0}
            )
            passing = {
                row.candidate.candidate_id
                for row in ranks["cb_pfr"] if row.physical.indicator == 0
            }
            passes_by_z.append(passing)
            for row in ranks["cb_pfr"]:
                violations_by_candidate[row.candidate.candidate_id].append(
                    row.physical.aggregate_violation
                )
        self.assertTrue(passes_by_z[2] <= passes_by_z[1] <= passes_by_z[0])
        for values in violations_by_candidate.values():
            self.assertEqual(values, sorted(values))

    def test_2_input_permutation_does_not_change_ranks_or_tie_groups(self):
        estimates = self._estimates([(0.5, 0.01)] * len(self.candidates))
        margins = {"response": 0.02}
        forward = rank_all_methods(
            self.model, self.candidates, estimates, [self.metric], margins
        )
        reverse = rank_all_methods(
            self.model, list(reversed(self.candidates)), estimates, [self.metric], margins
        )
        for method in forward:
            signature = lambda rows: [
                (row.candidate.candidate_id, row.rank, row.tie_group, row.ranking_key)
                for row in rows
            ]
            self.assertEqual(signature(forward[method]), signature(reverse[method]))
        self.assertEqual({row.rank for row in forward["cb_pfr"]}, {1})
        self.assertEqual({row.tie_group for row in forward["cb_pfr"]}, {1})

    def test_3_missing_and_non_finite_evidence_fail_closed_even_at_zero_weight(self):
        zero_weight_metric = MetricLimit(
            name="required", upper=1.0, z=1.0, scale=1.0, weight=0.0,
            uncertainty_kind="test_se", units="arbitrary",
        )
        missing = assess_physical([zero_weight_metric], None)
        self.assertEqual(missing.indicator, 1)
        self.assertTrue(math.isinf(missing.aggregate_violation))
        self.assertFalse(math.isnan(missing.aggregate_violation))

        candidate = self.candidates[0]
        invalid_estimate = PhysicalEstimate(
            candidate.candidate_id, {"required": (float("nan"), 0.0)}
        )
        invalid = assess_physical([zero_weight_metric], invalid_estimate)
        self.assertEqual(invalid.indicator, 1)
        self.assertTrue(math.isinf(invalid.aggregate_violation))

        ranking = rank_all_methods(
            self.model, [candidate], {}, [zero_weight_metric], {"required": 0.0}
        )
        selected = ranking["cb_pfr"][0]
        self.assertFalse(selected_is_conservatively_feasible(selected))
        self.assertEqual(selected.physical.indicator, 1)

    def test_4_zero_multiplier_matches_point_estimate_feasibility_first_rule(self):
        zero_z_metric = MetricLimit(
            name="response", upper=1.0, z=0.0, scale=0.1, weight=1.0,
            uncertainty_kind="test_between_run_sd", units="arbitrary",
        )
        rankings = rank_all_methods(
            self.model, self.candidates, self._estimates(),
            [zero_z_metric], {"response": 0.0},
        )
        signature = lambda rows: [
            (
                row.candidate.candidate_id, row.rank, row.tie_group,
                row.physical.indicator, row.physical.aggregate_violation,
            )
            for row in rows
        ]
        self.assertEqual(
            signature(rankings["cb_pfr"]), signature(rankings["point_estimate"])
        )
        cb = rankings["cb_pfr"]
        self.assertEqual(cb[0].physical.indicator, 0)
        infeasible = [row for row in cb if row.physical.indicator == 1]
        violations = [row.physical.aggregate_violation for row in infeasible]
        self.assertEqual(violations, sorted(violations))

    def test_duplicate_candidate_ids_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "unique"):
            rank_all_methods(
                self.model, [self.candidates[0], self.candidates[0]], {},
                [self.metric], {"response": 0.0},
            )


if __name__ == "__main__":
    unittest.main()
