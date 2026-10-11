#!/usr/bin/env python3
"""Analyze repeated solver trials with an explicit time-to-solution protocol.

Input CSV columns:
  instance_id,method,trial_id,success,per_attempt_wall_time_s
Optional columns:
  one_time_setup_s,anneal_time_s,objective_value,feasible

The primary TTS includes one-time setup plus repeated per-attempt wall time.
Device-only anneal time is reported separately when available. The script does
not itself establish quantum advantage: users must supply comparable run-level
measurements for the same instances, target solution criterion, and resource
accounting protocol.
"""
from __future__ import annotations

import argparse
import csv
import math
from collections import defaultdict
from pathlib import Path
from typing import Any

REQUIRED = {
    "instance_id", "method", "trial_id", "success", "per_attempt_wall_time_s"
}


def _as_bool(value: str, *, field: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "success"}:
        return True
    if normalized in {"0", "false", "no", "failure", "fail"}:
        return False
    raise ValueError(f"invalid {field} value {value!r}; use 0/1 or true/false")


def _positive_float(value: str, *, field: str, allow_zero: bool = False) -> float:
    number = float(value)
    if not math.isfinite(number) or number < 0 or (number == 0 and not allow_zero):
        qualifier = "nonnegative" if allow_zero else "positive"
        raise ValueError(f"{field} must be finite and {qualifier}, got {value!r}")
    return number


def _wilson(successes: int, trials: int, z: float = 1.959963984540054) -> tuple[float, float]:
    if trials <= 0:
        raise ValueError("trials must be positive")
    p = successes / trials
    denom = 1.0 + z * z / trials
    center = (p + z * z / (2 * trials)) / denom
    half = z * math.sqrt((p * (1 - p) / trials) + z * z / (4 * trials * trials)) / denom
    return max(0.0, center - half), min(1.0, center + half)


def _repetitions_for_target(success_probability: float, target_probability: float) -> int | None:
    if not 0 < target_probability < 1:
        raise ValueError("target_probability must be strictly between 0 and 1")
    if success_probability <= 0:
        return None
    if success_probability >= 1:
        return 1
    return math.ceil(math.log1p(-target_probability) / math.log1p(-success_probability))


def _tts(repetitions: int | None, per_attempt_s: float, setup_s: float) -> float | str:
    if repetitions is None:
        return "inf"
    return setup_s + repetitions * per_attempt_s


def analyze_rows(rows: list[dict[str, str]], target_probability: float = 0.99) -> list[dict[str, Any]]:
    if not rows:
        raise ValueError("input contains no trial rows")
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    seen: set[tuple[str, str, str]] = set()
    for line_number, row in enumerate(rows, start=2):
        missing = REQUIRED - set(row)
        if missing:
            raise ValueError(f"row {line_number} missing required columns: {sorted(missing)}")
        instance = row["instance_id"].strip()
        method = row["method"].strip()
        trial_id = row["trial_id"].strip()
        if not instance or not method or not trial_id:
            raise ValueError(f"row {line_number} has blank instance_id, method, or trial_id")
        unique = (instance, method, trial_id)
        if unique in seen:
            raise ValueError(f"duplicate trial key at row {line_number}: {unique}")
        seen.add(unique)
        success = _as_bool(row["success"], field="success")
        wall = _positive_float(row["per_attempt_wall_time_s"], field="per_attempt_wall_time_s")
        setup = _positive_float(row.get("one_time_setup_s", "") or "0", field="one_time_setup_s", allow_zero=True)
        anneal_text = row.get("anneal_time_s", "")
        anneal = None if not anneal_text.strip() else _positive_float(anneal_text, field="anneal_time_s", allow_zero=True)
        grouped[(instance, method)].append({
            "success": success, "wall": wall, "setup": setup, "anneal": anneal
        })

    output: list[dict[str, Any]] = []
    for (instance, method), trials in sorted(grouped.items()):
        n = len(trials)
        k = sum(int(t["success"]) for t in trials)
        p = k / n
        p_low, p_high = _wilson(k, n)
        reps = _repetitions_for_target(p, target_probability)
        # Invert the Wilson interval: a higher success probability means a lower TTS.
        reps_at_high = _repetitions_for_target(p_high, target_probability)
        reps_at_low = _repetitions_for_target(p_low, target_probability)
        mean_wall = sum(t["wall"] for t in trials) / n
        setup_values = [t["setup"] for t in trials]
        if max(setup_values) - min(setup_values) > 1e-12:
            raise ValueError(f"one_time_setup_s must be constant within {instance}/{method}")
        setup = setup_values[0]
        mean_anneal_values = [t["anneal"] for t in trials if t["anneal"] is not None]
        mean_anneal = sum(mean_anneal_values) / len(mean_anneal_values) if mean_anneal_values else None
        row = {
            "instance_id": instance,
            "method": method,
            "trials": n,
            "successes": k,
            "success_probability": p,
            "success_probability_wilson95_low": p_low,
            "success_probability_wilson95_high": p_high,
            "target_probability": target_probability,
            "repetitions_at_point_estimate": reps if reps is not None else "inf",
            "mean_per_attempt_wall_s": mean_wall,
            "one_time_setup_s": setup,
            "tts_target_wall_s": _tts(reps, mean_wall, setup),
            "tts_target_wall_wilson95_low_s": _tts(reps_at_high, mean_wall, setup),
            "tts_target_wall_wilson95_high_s": _tts(reps_at_low, mean_wall, setup),
            "mean_device_anneal_s": mean_anneal if mean_anneal is not None else "",
            "tts_target_device_anneal_s": (
                _tts(reps, mean_anneal, 0.0) if mean_anneal is not None else ""
            ),
        }
        output.append(row)
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="Run-level CSV with required schema")
    parser.add_argument("--output", required=True, type=Path, help="Summary CSV path (will not overwrite input)")
    parser.add_argument("--target-probability", type=float, default=0.99)
    args = parser.parse_args()
    if args.input.resolve() == args.output.resolve():
        parser.error("--output must not overwrite --input")
    if not args.input.is_file():
        parser.error(f"input file not found: {args.input}")
    with args.input.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    summary = analyze_rows(rows, args.target_probability)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(summary[0].keys()))
        writer.writeheader()
        writer.writerows(summary)
    print(f"Analyzed {len(rows)} trial rows into {len(summary)} instance/method groups.")
    print(f"Wrote {args.output}; target success probability={args.target_probability:.4f}")
    print("Interpretation guardrail: TTS estimates are only comparable when target criteria,")
    print("instance definitions, timing scope, and hardware/software resource accounting match.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
