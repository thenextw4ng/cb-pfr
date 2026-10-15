from __future__ import annotations

import math
from dataclasses import dataclass

from cbpfr.qubo import Candidate
from cbpfr.ranking import (
    MetricLimit,
    PhysicalEstimate,
    assess_physical,
    rank_all_methods,
    tie_groups,
)


@dataclass(frozen=True)
class TinyModel:
    """Minimal model contract for exercising the ranking layer."""
    def is_feasible(self, vector):
        return bool(vector[0])

    def energy(self, vector):
        return float(vector[1])


def metric(*, upper=10.0, z=1.0):
    return MetricLimit(
        name="F",
        upper=upper,
        z=z,
        scale=1.0,
        weight=1.0,
        uncertainty_kind="between-run SD (test fixture)",
        units="arb.",
    )


def estimate(candidate_id, mean, sd=0.2):
    return PhysicalEstimate(candidate_id, {"F": (mean, sd)})


def test_violation_is_non_decreasing_in_z_and_uncertainty():
    by_z = []
    for z in (0.0, 0.5, 1.0, 2.0):
        result = assess_physical([metric(upper=10.0, z=z)], estimate("near-limit", 9.95, 0.2))
        by_z.append(result.aggregate_violation)
    assert by_z == sorted(by_z)
    assert by_z[0] == 0.0
    assert by_z[-1] > by_z[0]

    by_uncertainty = []
    for uncertainty in (0.0, 0.02, 0.05, 0.1, 0.2, 0.5):
        result = assess_physical(
            [metric(upper=10.0, z=1.0)],
            estimate("near-limit", 9.95, uncertainty),
        )
        by_uncertainty.append(result.aggregate_violation)
    assert by_uncertainty == sorted(by_uncertainty)
    assert by_uncertainty[0] == 0.0
    assert by_uncertainty[-1] > by_uncertainty[0]


def test_missing_and_nonfinite_inputs_fail_closed():
    m = metric()
    missing = assess_physical([m], PhysicalEstimate("missing", {}))
    nan_value = assess_physical([m], estimate("nan", math.nan))
    nan_uncertainty = assess_physical([m], estimate("nan-sd", 2.0, math.nan))
    assert missing.indicator == 1
    assert missing.metric_assessments[0].status == "missing"
    assert nan_value.indicator == 1
    assert nan_uncertainty.indicator == 1
    assert math.isinf(missing.aggregate_violation)
    assert math.isinf(nan_value.aggregate_violation)
    assert math.isinf(nan_uncertainty.aggregate_violation)


def test_rank_order_and_tie_groups_are_input_permutation_invariant():
    model = TinyModel()
    candidates = [
        Candidate("zeta", (1, 0)),
        Candidate("alpha", (1, 0)),
        Candidate("middle", (1, 1)),
    ]
    estimates = {
        "zeta": estimate("zeta", 3.0),
        "alpha": estimate("alpha", 3.0),
        "middle": estimate("middle", 8.0),
    }
    metrics = [metric()]
    margins = {"F": 0.1}

    forward = rank_all_methods(model, candidates, estimates, metrics, margins)["cb_pfr"]
    reverse = rank_all_methods(model, list(reversed(candidates)), estimates, metrics, margins)["cb_pfr"]

    assert [item.candidate.candidate_id for item in forward] == [
        item.candidate.candidate_id for item in reverse
    ]
    forward_groups = [
        tuple(item.candidate.candidate_id for item in group) for group in tie_groups(forward)
    ]
    reverse_groups = [
        tuple(item.candidate.candidate_id for item in group) for group in tie_groups(reverse)
    ]
    assert forward_groups == reverse_groups
    assert ("alpha", "zeta") in forward_groups


def test_z_zero_matches_point_estimate_violation_rule():
    model = TinyModel()
    candidates = [
        Candidate("feasible-low", (1, 0)),
        Candidate("feasible-high", (1, 1)),
        Candidate("qubo-infeasible", (0, 0)),
    ]
    estimates = {
        "feasible-low": estimate("feasible-low", 9.8, 0.9),
        "feasible-high": estimate("feasible-high", 10.5, 0.9),
        "qubo-infeasible": estimate("qubo-infeasible", 8.0, 0.9),
    }
    results = rank_all_methods(
        model, candidates, estimates, [metric(z=0.0)], {"F": 0.0}
    )
    point = results["point_estimate"]
    cbpfr = results["cb_pfr"]
    assert [item.candidate.candidate_id for item in point] == [
        item.candidate.candidate_id for item in cbpfr
    ]
    assert [item.ranking_key for item in point] == [item.ranking_key for item in cbpfr]
    assert [item.physical.aggregate_violation for item in point] == [
        item.physical.aggregate_violation for item in cbpfr
    ]
