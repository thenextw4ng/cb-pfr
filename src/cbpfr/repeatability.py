"""Descriptive summaries for repeated optimizer rankings."""
from __future__ import annotations

from collections import Counter
from itertools import combinations
from typing import Sequence


def summarize_repeated_rankings(rankings: Sequence[Sequence[str]], *, top_k: int = 1) -> dict:
    """Summarize top-k overlap and candidate selection frequencies.

    Rankings must contain stable candidate IDs. This is descriptive agreement,
    not a probability guarantee or proof of optimizer optimality.
    """
    if isinstance(top_k, bool) or not isinstance(top_k, int) or top_k < 1:
        raise ValueError("top_k must be a positive integer")
    normalized = []
    for ranking in rankings:
        row = list(ranking)
        if len(row) != len(set(row)):
            raise ValueError("candidate IDs within each ranking must be unique")
        normalized.append(row)
    if not normalized:
        raise ValueError("at least one ranking is required")
    selected = [set(row[:top_k]) for row in normalized]
    pairs = []
    for left, right in combinations(selected, 2):
        union = left | right
        pairs.append(len(left & right) / len(union) if union else 1.0)
    frequency = Counter(candidate for group in selected for candidate in group)
    denom = len(selected)
    return {
        "run_count": len(normalized),
        "top_k": top_k,
        "pair_count": len(pairs),
        "mean_pairwise_top_k_jaccard": (sum(pairs) / len(pairs)) if pairs else 1.0,
        "exact_top_k_match_rate": (
            sum(1 for left, right in combinations(selected, 2) if left == right) / len(pairs)
            if pairs else 1.0
        ),
        "selection_frequency": {
            candidate: count / denom for candidate, count in sorted(frequency.items())
        },
        "interpretation": "descriptive agreement across recorded rankings; not a statistical guarantee",
    }
