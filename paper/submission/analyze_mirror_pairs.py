#!/usr/bin/env python3
"""Compute descriptive Welch intervals for mirror-label run-level differences.

No equivalence margin was declared before data acquisition. This script
therefore reports intervals only and deliberately does not infer equivalence.
Requires scipy.stats for Welch degrees of freedom.
"""
from __future__ import annotations
import argparse
import csv
import math
import statistics
from pathlib import Path
from scipy.stats import t

PAIRS = (("MMUU", "MUMU"), ("UMUM", "UUMM"))
METRICS = (("keff_mean", 1.0e5, "pcm"), ("fission_rate_peaking_factor", 1.0, "dimensionless"))


def welch_interval(a: list[float], b: list[float], confidence: float = 0.95) -> tuple[float, float, float, float]:
    if len(a) < 2 or len(b) < 2:
        raise ValueError("each label needs at least two independent run-level observations")
    if not all(math.isfinite(x) for x in a + b):
        raise ValueError("input observations must be finite")
    difference = statistics.mean(a) - statistics.mean(b)
    va, vb = statistics.variance(a), statistics.variance(b)
    se2a, se2b = va / len(a), vb / len(b)
    se = math.sqrt(se2a + se2b)
    if se == 0:
        return difference, difference, difference, math.inf
    df = (se2a + se2b) ** 2 / (se2a ** 2 / (len(a) - 1) + se2b ** 2 / (len(b) - 1))
    critical = float(t.ppf(0.5 + confidence / 2, df))
    return difference, difference - critical * se, difference + critical * se, df


def analyze(source: Path) -> list[dict[str, object]]:
    with source.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    by_label: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        by_label.setdefault(row["layout_signature"], []).append(row)
    expected = {label for pair in PAIRS for label in pair}
    if not expected <= set(by_label):
        raise ValueError(f"missing mirror labels: {sorted(expected-set(by_label))}")
    result = []
    for first, second in PAIRS:
        a_rows, b_rows = by_label[first], by_label[second]
        if len(a_rows) != 3 or len(b_rows) != 3:
            raise ValueError(f"expected exactly three runs per mirror label; got {first}={len(a_rows)}, {second}={len(b_rows)}")
        for field, multiplier, units in METRICS:
            a = [float(row[field]) for row in a_rows]
            b = [float(row[field]) for row in b_rows]
            delta, low, high, df = welch_interval(a, b)
            result.append({
                "pair": f"{first}-{second}",
                "first_label": first,
                "second_label": second,
                "metric": field,
                "units": units,
                "n_first": len(a),
                "n_second": len(b),
                "mean_first_raw": statistics.mean(a),
                "mean_second_raw": statistics.mean(b),
                "mean_difference": delta * multiplier,
                "welch_95ci_low": low * multiplier,
                "welch_95ci_high": high * multiplier,
                "welch_df": df,
                "equivalence_margin_prespecified": False,
                "equivalence_conclusion": "NOT_TESTED_MARGIN_NOT_PRESPECIFIED",
            })
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = analyze(args.input)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} descriptive mirror-pair intervals to {args.output}")
    print("No equivalence conclusion made: margins were not specified before data acquisition.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
