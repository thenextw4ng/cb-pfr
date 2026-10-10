"""Thin integration boundary between QUBO candidates and CB-PFR ranking.

This module does not run a physical simulator. Callers must supply explicitly
labelled evaluation records; synthetic fixtures must never be presented as
OpenMC results.
"""
from __future__ import annotations

from dataclasses import asdict
from typing import Mapping, Sequence

from .qubo import Candidate, QuboModel
from .ranking import MetricLimit, PhysicalEstimate, RankedCandidate, rank_all_methods


def rank_candidate_batch(
    model: QuboModel,
    candidates: Sequence[Candidate],
    estimates: Mapping[str, PhysicalEstimate],
    metrics: Sequence[MetricLimit],
    uniform_margins: Mapping[str, float],
) -> dict[str, list[RankedCandidate]]:
    """Rank one candidate batch using all existing comparison methods.

    This adapter intentionally delegates ranking to the existing CB-PFR
    implementation and does not reinterpret metric bounds or uncertainties.
    """
    if not candidates:
        raise ValueError("candidate batch cannot be empty")
    ids = [candidate.candidate_id for candidate in candidates]
    if any(not isinstance(candidate_id, str) or not candidate_id.strip() for candidate_id in ids):
        raise ValueError("candidate IDs must be non-empty strings")
    if len(set(ids)) != len(ids):
        raise ValueError("candidate IDs must be unique within a batch")
    unexpected_estimates = set(estimates) - set(ids)
    if unexpected_estimates:
        raise ValueError(f"estimates contain unknown candidate IDs: {sorted(unexpected_estimates)}")
    for key, estimate in estimates.items():
        if key != estimate.candidate_id:
            raise ValueError(
                f"estimate mapping key {key!r} does not match "
                f"estimate candidate_id {estimate.candidate_id!r}"
            )
    return rank_all_methods(model, candidates, estimates, metrics, uniform_margins)


def ranking_to_records(
    rankings: Mapping[str, Sequence[RankedCandidate]],
    *,
    data_kind: str,
) -> list[dict[str, object]]:
    """Convert rankings to JSON/CSV-friendly records with provenance labels."""
    if data_kind not in {"synthetic", "mock", "physical"}:
        raise ValueError("data_kind must be synthetic, mock, or physical")
    records: list[dict[str, object]] = []
    for method, ranked_candidates in rankings.items():
        for rank, item in enumerate(ranked_candidates, start=1):
            physical = None
            if item.physical is not None:
                physical = {
                    "indicator": item.physical.indicator,
                    "aggregate_violation": (
                        item.physical.aggregate_violation
                        if item.physical.aggregate_violation != float("inf")
                        else None
                    ),
                    "metrics": [asdict(metric) for metric in item.physical.metric_assessments],
                }
            records.append({
                "data_kind": data_kind,
                "method": method,
                "rank": rank,
                "candidate_id": item.candidate.candidate_id,
                "candidate_vector": list(item.candidate.vector),
                "qubo_feasible": item.qubo_indicator == 0,
                "qubo_energy": item.qubo_energy,
                "physical_assessment": physical,
                "physical_simulation_performed": data_kind == "physical",
            })
    return records
