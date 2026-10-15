from __future__ import annotations
import math
import unittest
from dataclasses import dataclass

from cbpfr.qubo import Candidate
from cbpfr.ranking import MetricLimit, PhysicalEstimate, assess_physical, rank_all_methods, tie_groups


@dataclass(frozen=True)
class TinyModel:
    def is_feasible(self, vector):
        return bool(vector[0])
    def energy(self, vector):
        return float(vector[1])


def metric(*, upper=10.0, z=1.0):
    return MetricLimit(name="F", upper=upper, z=z, scale=1.0, weight=1.0,
                       uncertainty_kind="between-run SD (test fixture)", units="arb.")


def estimate(candidate_id, mean, sd=0.2):
    return PhysicalEstimate(candidate_id, {"F": (mean, sd)})


class TestCBPFRProperties(unittest.TestCase):
    def test_violation_is_non_decreasing_in_z_and_uncertainty(self):
        by_z = [assess_physical([metric(z=z)], estimate("near-limit", 9.95, 0.2)).aggregate_violation
                for z in (0.0, 0.5, 1.0, 2.0)]
        self.assertEqual(by_z, sorted(by_z))
        self.assertEqual(by_z[0], 0.0)
        self.assertGreater(by_z[-1], by_z[0])
        by_sd = [assess_physical([metric(z=1.0)], estimate("near-limit", 9.95, sd)).aggregate_violation
                 for sd in (0.0, 0.02, 0.05, 0.1, 0.2, 0.5)]
        self.assertEqual(by_sd, sorted(by_sd))
        self.assertEqual(by_sd[0], 0.0)
        self.assertGreater(by_sd[-1], by_sd[0])

    def test_missing_and_nonfinite_inputs_fail_closed(self):
        m = metric()
        missing = assess_physical([m], PhysicalEstimate("missing", {}))
        nan_value = assess_physical([m], estimate("nan", math.nan))
        nan_uncertainty = assess_physical([m], estimate("nan-sd", 2.0, math.nan))
        self.assertEqual(missing.indicator, 1)
        self.assertEqual(missing.metric_assessments[0].status, "missing")
        self.assertEqual(nan_value.indicator, 1)
        self.assertEqual(nan_uncertainty.indicator, 1)
        self.assertTrue(math.isinf(missing.aggregate_violation))
        self.assertTrue(math.isinf(nan_value.aggregate_violation))
        self.assertTrue(math.isinf(nan_uncertainty.aggregate_violation))

    def test_rank_order_and_tie_groups_are_input_permutation_invariant(self):
        model = TinyModel()
        candidates = [Candidate("zeta", (1, 0)), Candidate("alpha", (1, 0)), Candidate("middle", (1, 1))]
        estimates = {"zeta": estimate("zeta", 3.0), "alpha": estimate("alpha", 3.0),
                     "middle": estimate("middle", 8.0)}
        forward = rank_all_methods(model, candidates, estimates, [metric()], {"F": 0.1})["cb_pfr"]
        reverse = rank_all_methods(model, list(reversed(candidates)), estimates, [metric()], {"F": 0.1})["cb_pfr"]
        self.assertEqual([x.candidate.candidate_id for x in forward],
                         [x.candidate.candidate_id for x in reverse])
        forward_groups = [tuple(x.candidate.candidate_id for x in g) for g in tie_groups(forward)]
        reverse_groups = [tuple(x.candidate.candidate_id for x in g) for g in tie_groups(reverse)]
        self.assertEqual(forward_groups, reverse_groups)
        self.assertIn(("alpha", "zeta"), forward_groups)

    def test_z_zero_matches_point_estimate_violation_rule(self):
        model = TinyModel()
        candidates = [Candidate("feasible-low", (1, 0)), Candidate("feasible-high", (1, 1)),
                      Candidate("qubo-infeasible", (0, 0))]
        estimates = {"feasible-low": estimate("feasible-low", 9.8, 0.9),
                     "feasible-high": estimate("feasible-high", 10.5, 0.9),
                     "qubo-infeasible": estimate("qubo-infeasible", 8.0, 0.9)}
        results = rank_all_methods(model, candidates, estimates, [metric(z=0.0)], {"F": 0.0})
        point, cbpfr = results["point_estimate"], results["cb_pfr"]
        self.assertEqual([x.candidate.candidate_id for x in point],
                         [x.candidate.candidate_id for x in cbpfr])
        self.assertEqual([x.ranking_key for x in point], [x.ranking_key for x in cbpfr])
        self.assertEqual([x.physical.aggregate_violation for x in point],
                         [x.physical.aggregate_violation for x in cbpfr])


if __name__ == "__main__":
    unittest.main()
