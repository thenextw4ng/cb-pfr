"""Descriptive stability summaries for repeated optimizer rankings."""
from __future__ import annotations

from collections import Counter
from itertools import combinations
from typing import Sequence


def summarize_repeated_rankings(rankings: Sequence[Sequence[str]], *, top_k: int = 1) -> dict:
    """Summarize top-1 frequency and pairwise top-k overlap.

    The function reports descriptive agreement across supplied rankings. It is
    not a probability guarantee or proof of global optimizer optimality.
    """
    if isinstance(top_k, bool) or not isinstance(top_k, int) or top_k < 1:
        raise ValueError("top_k must be a positive integer")
    if isinstance(rankings, (str, bytes)) or not rankings:
        raise ValueError("at least one run is required")
    normalized = []
    for ranking in rankings:
        if isinstance(ranking, (str, bytes)):
            raise ValueError("a run must be a sequence of candidate IDs, not a string")
        row = list(ranking)
        if not row:
            raise ValueError("ranking cannot be empty")
        if any(not isinstance(candidate, str) or not candidate.strip() for candidate in row):
            raise ValueError("candidate IDs must be non-empty strings")
        if len(row) != len(set(row)):
            raise ValueError("duplicate candidate IDs within one ranking are not allowed")
        normalized.append(row)

    selected = [set(row[:top_k]) for row in normalized]
    pairs = []
    exact_matches = 0
    for left, right in combinations(selected, 2):
        union = left | right
        pairs.append(len(left & right) / len(union) if union else 1.0)
        exact_matches += left == right

    top1_counts = Counter(row[0] for row in normalized)
    top_k_counts = Counter(candidate for group in selected for candidate in group)
    run_count = len(normalized)
    pair_count = len(pairs)
    top1_selection_counts = dict(sorted(top1_counts.items()))
    return {
        "run_count": run_count,
        "top_k": top_k,
        "pair_count": pair_count,
        "top1_selection_counts": top1_selection_counts,
        "top1_selection_frequencies": {
            candidate: count / run_count for candidate, count in sorted(top1_counts.items())
        },
        "top1_dominance": max(top1_counts.values()) / run_count,
        "top_k_selection_counts": dict(sorted(top_k_counts.items())),
        "top_k_selection_frequencies": {
            candidate: count / run_count for candidate, count in sorted(top_k_counts.items())
        },
        "selection_frequency": {
            candidate: count / run_count for candidate, count in sorted(top_k_counts.items())
        },
        "mean_pairwise_top_k_jaccard": (sum(pairs) / pair_count) if pairs else 1.0,
        "exact_top_k_match_rate": (exact_matches / pair_count) if pair_count else 1.0,
        "interpretation": (
            "descriptive agreement across recorded rankings; not a global-optimum certificate "
            "or statistical guarantee"
        ),
    }
