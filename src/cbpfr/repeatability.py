"""Descriptive repeatability metrics for repeated optimizer ranking runs.

These summaries quantify observed run-to-run consistency only. They do not
certify global optimality, physical feasibility, or statistical confidence.
"""
from __future__ import annotations

from itertools import combinations
from typing import Sequence


def summarize_repeated_rankings(
    runs: Sequence[Sequence[str]], *, top_k: int = 1
) -> dict[str, object]:
    """Summarize candidate selection stability across independent ranking runs.

    Each run is an ordered sequence of candidate IDs, best-ranked first.
    Candidate IDs must be unique within a run. The top-k Jaccard statistic
    compares sets, so it measures membership overlap rather than rank order.
    """
    if not runs:
        raise ValueError("at least one run is required")
    if isinstance(top_k, bool) or not isinstance(top_k, int) or top_k < 1:
        raise ValueError("top_k must be a positive integer")

    normalized: list[tuple[str, ...]] = []
    for run_index, run in enumerate(runs):
        if isinstance(run, (str, bytes)):
            raise ValueError(f"run {run_index} must be a sequence of candidate IDs, not a string")
        row = tuple(run)
        if not row:
            raise ValueError(f"run {run_index} cannot be empty")
        if any(not isinstance(candidate_id, str) or not candidate_id.strip() for candidate_id in row):
            raise ValueError(f"run {run_index} contains an empty or invalid candidate ID")
        if len(set(row)) != len(row):
            raise ValueError(f"run {run_index} contains duplicate candidate IDs")
        normalized.append(row)

    top1_counts: dict[str, int] = {}
    topk_counts: dict[str, int] = {}
    topk_sets: list[set[str]] = []
    for run in normalized:
        top1_counts[run[0]] = top1_counts.get(run[0], 0) + 1
        selected = set(run[:top_k])
        topk_sets.append(selected)
        for candidate_id in selected:
            topk_counts[candidate_id] = topk_counts.get(candidate_id, 0) + 1

    run_count = len(normalized)
    pairwise_jaccard: list[float] = []
    for left, right in combinations(topk_sets, 2):
        union = left | right
        pairwise_jaccard.append(len(left & right) / len(union) if union else 1.0)

    return {
        "run_count": run_count,
        "top_k": top_k,
        "top1_selection_counts": dict(sorted(top1_counts.items())),
        "top1_selection_frequencies": {
            candidate_id: count / run_count
            for candidate_id, count in sorted(top1_counts.items())
        },
        "top_k_selection_counts": dict(sorted(topk_counts.items())),
        "top_k_selection_frequencies": {
            candidate_id: count / run_count
            for candidate_id, count in sorted(topk_counts.items())
        },
        "top1_dominance": max(top1_counts.values()) / run_count,
        "mean_pairwise_top_k_jaccard": (
            sum(pairwise_jaccard) / len(pairwise_jaccard)
            if pairwise_jaccard
            else 1.0
        ),
        "interpretation": (
            "descriptive repeatability only; not a global-optimum certificate "
            "or physical-validity claim"
        ),
    }
