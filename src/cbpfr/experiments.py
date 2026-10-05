"""Deterministic helpers for the frozen synthetic benchmark."""
from __future__ import annotations
from typing import Mapping, Sequence

def held_out_lookup(selection_ids: Mapping[str,str], truth: Mapping[str,float]) -> dict[str,float]:
    missing=[candidate_id for candidate_id in selection_ids.values() if candidate_id not in truth]
    if missing: raise KeyError(f"selected candidates missing from held-out truth: {missing}")
    return {method: truth[candidate_id] for method,candidate_id in selection_ids.items()}

def require_equal_evaluation_budget(budgets: Mapping[str,int], expected: int | None = None) -> None:
    values=list(budgets.values())
    if not values or len(set(values)) != 1: raise ValueError(f"methods must have equal evaluation budgets: {dict(budgets)}")
    if expected is not None and values[0] != expected: raise ValueError(f"evaluation budget {values[0]} does not equal expected {expected}")

def paired_binary_difference(left: Sequence[bool], right: Sequence[bool]) -> dict[str,int]:
    if len(left)!=len(right): raise ValueError("paired outcomes must have equal length")
    left_only=sum(a and not b for a,b in zip(left,right)); right_only=sum((not a) and b for a,b in zip(left,right)); ties=len(left)-left_only-right_only
    return {"left_only":left_only,"right_only":right_only,"ties":ties,"discordant":left_only+right_only}
