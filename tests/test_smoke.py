import math
import tempfile
import unittest
from pathlib import Path

from cbpfr.experiments import held_out_lookup, paired_binary_difference, require_equal_evaluation_budget
from cbpfr.qubo import CandidateMappingError, CoreSpec, build_usmanov_style_qubo, enumerate_feasible_candidates
from cbpfr.ranking import MetricLimit, PhysicalEstimate, assess_physical, rank_all_methods, selected_is_conservatively_feasible


class CBPFRTests(unittest.TestCase):
    def setUp(self):
        self.spec = CoreSpec(
            name="seven_position_toy",
            positions=tuple(f"p{i}" for i in range(7)),
            boundary=frozenset({f"p{i}" for i in range(1, 7)}),
            inner=frozenset({"p0"}),
            edges=tuple((f"p{i}", f"p{1 + (i % 6)}") for i in range(1, 7)),
            inventory=(3, 3, 1),
        )
        self.model = build_usmanov_style_qubo(self.spec)
        self.candidates = enumerate_feasible_candidates(self.model)

    def metric(self, **kwargs):
        base=dict(name="response", upper=1.0, z=1.0, scale=1.0, weight=1.0, uncertainty_kind="known_se")
        base.update(kwargs)
        return MetricLimit(**base)

    def test_exact_toy_core_has_expected_size(self):
        self.assertEqual(self.model.variable_count, 21)
        self.assertEqual(len(self.candidates), 20)

    def test_qubo_energy_matches_direct_penalty(self):
        for candidate in self.candidates:
            self.assertAlmostEqual(
                self.model.energy(candidate.vector),
                sum(self.model.direct_penalty_terms(candidate.vector).values()),
            )

    def test_all_enumerated_candidates_are_feasible(self):
        self.assertTrue(all(self.model.is_feasible(c.vector) for c in self.candidates))

    def test_missing_metric_fails_closed(self):
        result=assess_physical([self.metric()], None)
        self.assertEqual(result.indicator, 1)
        self.assertEqual(result.metric_assessments[0].status, "missing")
        self.assertTrue(math.isinf(result.aggregate_violation))

    def test_negative_nan_and_infinite_uncertainty_fail_closed(self):
        metric=self.metric()
        for uncertainty in (-1.0, math.nan, math.inf):
            result=assess_physical([metric], PhysicalEstimate("x", {"response": (0.5, uncertainty)}))
            self.assertEqual(result.indicator, 1)
            self.assertIn(result.metric_assessments[0].status, {"nonfinite_or_negative", "invalid_width"})

    def test_nonfinite_mean_fails_closed(self):
        result=assess_physical([self.metric()], PhysicalEstimate("x", {"response": (math.nan, 0.1)}))
        self.assertEqual(result.metric_assessments[0].status, "nonfinite_or_negative")

    def test_overflowed_bounds_fail_closed(self):
        result=assess_physical([self.metric(z=2.0)], PhysicalEstimate("x", {"response": (1e308, 1e308)}))
        self.assertEqual(result.indicator, 1)
        self.assertEqual(result.metric_assessments[0].status, "invalid_width")

    def test_malformed_estimate_fails_closed(self):
        for supplied in ((0.5,), (0.5, 0.1, 0.2), ("0.5", 0.1)):
            with self.subTest(supplied=supplied):
                result=assess_physical([self.metric()], PhysicalEstimate("x", {"response": supplied}))
                self.assertEqual(result.indicator, 1)
                self.assertEqual(result.metric_assessments[0].status, "invalid_estimate")

    def test_upper_and_lower_bounds_are_conservative(self):
        metric=self.metric(lower=0.2, upper=0.8, z=2.0)
        result=assess_physical([metric], PhysicalEstimate("x", {"response": (0.5, 0.1)}))
        a=result.metric_assessments[0]
        self.assertAlmostEqual(a.lower_bound, 0.3)
        self.assertAlmostEqual(a.upper_bound, 0.7)
        self.assertTrue(a.passes)

        result=assess_physical([metric], PhysicalEstimate("x", {"response": (0.75, 0.1)}))
        self.assertFalse(result.metric_assessments[0].passes)
        self.assertAlmostEqual(result.metric_assessments[0].violation, 0.15)

    def test_zero_z_reduces_to_point_estimate(self):
        metric=self.metric(z=0.0)
        result=assess_physical([metric], PhysicalEstimate("x", {"response": (0.95, 0.2)}))
        self.assertAlmostEqual(result.metric_assessments[0].lower_bound, 0.95)
        self.assertAlmostEqual(result.metric_assessments[0].upper_bound, 0.95)
        self.assertTrue(result.metric_assessments[0].passes)

    def test_uniform_margin_overrides_candidate_uncertainty(self):
        metric=self.metric(upper=1.0, z=1.0)
        estimate=PhysicalEstimate("x", {"response": (0.95, 0.001)})
        result=assess_physical([metric], estimate, uniform_margins={"response": 0.1})
        self.assertEqual(result.metric_assessments[0].upper_bound, 1.05)
        self.assertEqual(result.indicator, 1)

    def test_multiple_metrics_weighted_violation(self):
        metrics=[
            self.metric(name="a", upper=1.0, scale=0.1, weight=2.0),
            self.metric(name="b", lower=0.0, scale=0.2, weight=1.0),
        ]
        estimate=PhysicalEstimate("x", {"a": (1.05, 0.0), "b": (-0.1, 0.0)})
        result=assess_physical(metrics, estimate)
        self.assertAlmostEqual(result.aggregate_violation, 2.0*0.5 + 0.5)

    def test_ranking_tie_break_is_deterministic(self):
        candidates=self.candidates[:3]
        estimates={c.candidate_id: PhysicalEstimate(c.candidate_id, {"response": (0.5,0.01)}) for c in candidates}
        result=rank_all_methods(self.model,candidates,estimates,[self.metric()],{"response":0.0})
        self.assertEqual(result["cb_pfr"][0].input_index,0)
        self.assertEqual(result["point_estimate"][0].input_index,0)

    def test_missing_candidate_estimate_is_ranked_as_failed(self):
        candidates=self.candidates[:2]
        estimates={candidates[1].candidate_id: PhysicalEstimate(candidates[1].candidate_id, {"response": (0.5,0.01)})}
        result=rank_all_methods(self.model,candidates,estimates,[self.metric()],{"response":0.0})
        self.assertEqual(result["cb_pfr"][0].candidate.candidate_id,candidates[1].candidate_id)
        self.assertEqual(result["cb_pfr"][1].physical.metric_assessments[0].status,"missing")

    def test_no_candidate_passing_is_not_reported_as_feasible(self):
        candidates=self.candidates[:3]
        estimates={c.candidate_id: PhysicalEstimate(c.candidate_id, {"response": (2.0,0.0)}) for c in candidates}
        result=rank_all_methods(self.model,candidates,estimates,[self.metric()],{"response":0.0})
        self.assertFalse(selected_is_conservatively_feasible(result["cb_pfr"][0]))
        self.assertEqual(result["cb_pfr"][0].physical.indicator,1)

    def test_invalid_uniform_margin_configuration_is_rejected(self):
        candidates=self.candidates[:1]
        estimates={candidates[0].candidate_id: PhysicalEstimate(candidates[0].candidate_id, {"response": (0.5,0.1)})}
        with self.assertRaises(ValueError):
            rank_all_methods(self.model,candidates,estimates,[self.metric()],{"wrong":0.1})

    def test_metric_rejects_nonfinite_limits_and_parameters(self):
        for kwargs in (
            {"upper": math.nan}, {"lower": -math.inf}, {"z": math.inf},
            {"scale": math.nan}, {"weight": math.inf},
        ):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                self.metric(**kwargs)

    def test_metric_rejects_empty_name(self):
        with self.assertRaisesRegex(ValueError, "name"):
            self.metric(name="  ")

    def test_duplicate_metric_names_are_rejected(self):
        candidates=self.candidates[:1]
        estimates={candidates[0].candidate_id: PhysicalEstimate(candidates[0].candidate_id, {"response": (0.5,0.1)})}
        with self.assertRaisesRegex(ValueError, "unique"):
            rank_all_methods(self.model,candidates,estimates,[self.metric(), self.metric()],{"response":0.0})

    def test_nonfinite_uniform_margin_is_rejected(self):
        candidates=self.candidates[:1]
        estimates={candidates[0].candidate_id: PhysicalEstimate(candidates[0].candidate_id, {"response": (0.5,0.1)})}
        for value in (math.nan, math.inf, -math.inf, -0.1):
            with self.subTest(value=value), self.assertRaises(ValueError):
                rank_all_methods(self.model,candidates,estimates,[self.metric()],{"response":value})

    def test_equal_budget_guard(self):
        require_equal_evaluation_budget({"a":12,"b":12},12)
        with self.assertRaises(ValueError): require_equal_evaluation_budget({"a":12,"b":11},12)

    def test_held_out_lookup_rejects_missing_truth(self):
        with self.assertRaises(KeyError): held_out_lookup({"cb_pfr":"x"}, {})
        self.assertEqual(held_out_lookup({"cb_pfr":"x"},{"x":0.9}),{"cb_pfr":0.9})

    def test_paired_difference_counts(self):
        self.assertEqual(
            paired_binary_difference([True,False,True,False],[False,False,True,True]),
            {"left_only":1,"right_only":1,"ties":2,"discordant":2},
        )

    def test_candidate_validation_rejects_nonbinary_and_bad_length(self):
        with self.assertRaises(CandidateMappingError): self.model.energy([0] * 20)
        with self.assertRaises(CandidateMappingError): self.model.energy([0] * 21 + [1])
        with self.assertRaises(CandidateMappingError): self.model.energy([0] * 20 + [2])

if __name__ == "__main__":
    unittest.main()
