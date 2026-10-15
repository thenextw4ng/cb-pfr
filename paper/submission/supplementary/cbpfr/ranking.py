"""Confidence-Bounded Physical Feasibility Ranking (CB-PFR).

This module implements the working paper's operational rule. Its bounds are
not labeled confidence intervals, safety margins, or reactor safety evidence.
The caller supplies units, acceptance limits, uncertainty meanings, and all
metric values explicitly.
"""
from __future__ import annotations
from dataclasses import dataclass
import math
from typing import Mapping, Sequence
from .qubo import Candidate, QuboModel

@dataclass(frozen=True)
class MetricLimit:
    name: str
    lower: float | None = None
    upper: float | None = None
    z: float = 0.0
    scale: float = 1.0
    weight: float = 1.0
    uncertainty_kind: str = "unspecified"
    units: str = "unspecified"
    bound_kind: str = "operational_heuristic"
    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("metric name must be a non-empty string")
        if self.lower is None and self.upper is None:
            raise ValueError(f"metric {self.name} needs a lower and/or upper limit")
        for label, value in (("lower", self.lower), ("upper", self.upper), ("z", self.z), ("scale", self.scale), ("weight", self.weight)):
            if value is None:
                continue
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                raise ValueError(f"metric {self.name} {label} must be a finite real number")
        if self.lower is not None and self.upper is not None and self.lower > self.upper:
            raise ValueError(f"metric {self.name} has lower limit above upper limit")
        if self.z < 0 or self.scale <= 0 or self.weight < 0:
            raise ValueError(f"metric {self.name} has invalid z, scale, or weight")
        if not isinstance(self.uncertainty_kind, str) or not self.uncertainty_kind.strip() or self.uncertainty_kind == "unspecified":
            raise ValueError(f"metric {self.name} must identify uncertainty_kind")
        if self.bound_kind not in {"operational_heuristic", "known_normal_one_sided"}:
            raise ValueError(f"metric {self.name} has unsupported bound_kind; it must not imply an untested confidence claim")

@dataclass(frozen=True)
class PhysicalEstimate:
    candidate_id: str
    values: Mapping[str, tuple[float, float]]

@dataclass(frozen=True)
class MetricAssessment:
    name: str
    mean: float | None
    uncertainty: float | None
    lower_bound: float | None
    upper_bound: float | None
    violation: float
    normalized_violation: float
    passes: bool
    status: str

@dataclass(frozen=True)
class PhysicalAssessment:
    metric_assessments: tuple[MetricAssessment, ...]
    indicator: int
    aggregate_violation: float

@dataclass(frozen=True)
class RankedCandidate:
    method: str
    candidate: Candidate
    qubo_indicator: int
    qubo_energy: float
    physical: PhysicalAssessment | None
    ranking_key: tuple[float | int, ...]
    rank: int
    tie_group: int

def _assessment_for_metric(metric: MetricLimit, supplied: tuple[float, float] | None, width_override: float | None) -> MetricAssessment:
    if supplied is None:
        return MetricAssessment(metric.name, None, None, None, None, math.inf, math.inf, False, "missing")
    mean, uncertainty = supplied
    if (isinstance(mean, bool) or isinstance(uncertainty, bool)
            or not isinstance(mean, (int, float)) or not isinstance(uncertainty, (int, float))
            or not math.isfinite(mean) or not math.isfinite(uncertainty) or uncertainty < 0):
        return MetricAssessment(metric.name, mean if isinstance(mean, (int, float)) else None,
                                uncertainty if isinstance(uncertainty, (int, float)) else None,
                                None, None, math.inf, math.inf, False, "nonfinite_or_negative")
    width = metric.z * uncertainty if width_override is None else width_override
    if not math.isfinite(width) or width < 0:
        return MetricAssessment(metric.name, mean, uncertainty, None, None, math.inf, math.inf, False, "invalid_width")
    lower_bound, upper_bound = mean - width, mean + width
    violation = 0.0
    if metric.lower is not None:
        violation += max(0.0, metric.lower - lower_bound)
    if metric.upper is not None:
        violation += max(0.0, upper_bound - metric.upper)
    return MetricAssessment(metric.name, mean, uncertainty, lower_bound, upper_bound, violation, violation / metric.scale, violation == 0.0, "evaluated")

def assess_physical(metrics: Sequence[MetricLimit], estimate: PhysicalEstimate | None, *, uniform_margins: Mapping[str, float] | None = None) -> PhysicalAssessment:
    assessments = []
    for metric in metrics:
        width = None if uniform_margins is None else uniform_margins.get(metric.name)
        assessments.append(_assessment_for_metric(metric, None if estimate is None else estimate.values.get(metric.name), width))
    indicator = int(any(not assessment.passes for assessment in assessments))
    # Missing or invalid required evidence is a hard failure even when a
    # metric has zero weight; prevent 0 * inf from creating NaN.
    if any(not math.isfinite(assessment.normalized_violation) for assessment in assessments):
        aggregate = math.inf
    else:
        aggregate = sum(metric.weight * assessment.normalized_violation for metric, assessment in zip(metrics, assessments))
    return PhysicalAssessment(tuple(assessments), indicator, aggregate)

def _rank(method: str, model: QuboModel, candidates: Sequence[Candidate], estimates: Mapping[str, PhysicalEstimate], metrics: Sequence[MetricLimit], *, mode: str, uniform_margins: Mapping[str, float] | None = None) -> list[RankedCandidate]:
    """Rank candidates without turning equal substantive scores into preferences."""
    scored: list[tuple[tuple[float | int, ...], Candidate, int, float, PhysicalAssessment | None]] = []
    for candidate in candidates:
        qubo_indicator = int(not model.is_feasible(candidate.vector))
        energy = model.energy(candidate.vector)
        if mode == "qubo":
            physical = None
            key: tuple[float | int, ...] = (qubo_indicator, energy)
        else:
            if mode == "point":
                margins = {metric.name: 0.0 for metric in metrics}
            elif mode == "uniform":
                margins = uniform_margins
            elif mode == "cbpfr":
                margins = None
            else:
                raise ValueError(f"unknown ranking mode: {mode}")
            physical = assess_physical(metrics, estimates.get(candidate.candidate_id), uniform_margins=margins)
            # Feasibility-first (Deb-style) ordering: feasibility, then lower
            # violation. Energy only breaks ties between feasible candidates;
            # it never chooses one infeasible candidate over another.
            objective_component = energy if physical.indicator == 0 else 0.0
            key = (qubo_indicator, physical.indicator, physical.aggregate_violation, objective_component)
        scored.append((key, candidate, qubo_indicator, energy, physical))

    # The identifier orders records for reproducible display only. Ranking and
    # tie groups are computed from the substantive score and are permutation-invariant.
    scored.sort(key=lambda row: (row[0], row[1].candidate_id))
    ranked: list[RankedCandidate] = []
    previous_key: tuple[float | int, ...] | None = None
    current_rank = 0
    current_tie_group = 0
    for position, (key, candidate, qubo_indicator, energy, physical) in enumerate(scored, start=1):
        if previous_key is None or key != previous_key:
            current_rank = position
            current_tie_group += 1
            previous_key = key
        ranked.append(RankedCandidate(
            method=method,
            candidate=candidate,
            qubo_indicator=qubo_indicator,
            qubo_energy=energy,
            physical=physical,
            ranking_key=key,
            rank=current_rank,
            tie_group=current_tie_group,
        ))
    return ranked

def rank_all_methods(model: QuboModel, candidates: Sequence[Candidate], estimates: Mapping[str, PhysicalEstimate], metrics: Sequence[MetricLimit], uniform_margins: Mapping[str, float]) -> dict[str, list[RankedCandidate]]:
    if not candidates:
        raise ValueError("candidate pool cannot be empty")
    candidate_ids = [candidate.candidate_id for candidate in candidates]
    if any(not isinstance(candidate_id, str) or not candidate_id.strip() for candidate_id in candidate_ids):
        raise ValueError("candidate IDs must be non-empty strings")
    if len(candidate_ids) != len(set(candidate_ids)):
        raise ValueError("candidate IDs must be unique")
    metric_names = [metric.name for metric in metrics]
    if len(metric_names) != len(set(metric_names)):
        raise ValueError("metric names must be unique")
    if not metrics:
        raise ValueError("at least one physical metric must be declared")
    expected = {metric.name for metric in metrics}
    if set(uniform_margins) != expected:
        raise ValueError("uniform margins must give one value for every metric")
    if any(isinstance(value, bool) or not isinstance(value, (int, float))
           or not math.isfinite(value) or value < 0 for value in uniform_margins.values()):
        raise ValueError("uniform margins must be finite, numeric, and nonnegative")
    return {
        "qubo_only": _rank("qubo_only", model, candidates, estimates, metrics, mode="qubo"),
        "point_estimate": _rank("point_estimate", model, candidates, estimates, metrics, mode="point"),
        "cb_pfr": _rank("cb_pfr", model, candidates, estimates, metrics, mode="cbpfr"),
        "uniform_margin": _rank("uniform_margin", model, candidates, estimates, metrics, mode="uniform", uniform_margins=uniform_margins),
    }

def selected_is_conservatively_feasible(result: RankedCandidate) -> bool:
    return result.qubo_indicator == 0 and result.physical is not None and result.physical.indicator == 0
