#!/usr/bin/env python3
"""Deterministic audit recomputation for S4 R1 paired binary outcomes.

Usage:
  python paired_audit.py per_seed_results.csv --seed 20261115 --resamples 50000

This is an audit recomputation. It is not asserted to reproduce the historical
paper intervals until the original historical bootstrap settings are recovered.
"""
import argparse
import csv
import random
from collections import defaultdict
from math import comb

METHODS = ("cb_pfr", "point_estimate", "uniform_margin", "qubo_only")

def exact_sign_p(two_methods):
    """Two-sided exact binomial sign-test p-value among discordant pairs."""
    wins_a, wins_b = two_methods
    n = wins_a + wins_b
    if n == 0:
        return 1.0
    k = min(wins_a, wins_b)
    tail = sum(comb(n, i) for i in range(k + 1)) / (2 ** n)
    return min(1.0, 2.0 * tail)

def quantile(values, p):
    values = sorted(values)
    x = (len(values) - 1) * p
    lo = int(x)
    hi = min(lo + 1, len(values) - 1)
    return values[lo] + (values[hi] - values[lo]) * (x - lo)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv_path")
    ap.add_argument("--seed", type=int, default=20261115)
    ap.add_argument("--resamples", type=int, default=50000)
    args = ap.parse_args()

    pools = defaultdict(dict)
    with open(args.csv_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            trial = int(row["trial_index"])
            method = row["method"]
            value = row["selected_true_feasible"].strip().lower()
            pools[trial][method] = int(value in ("true", "1", "yes"))

    ordered = [pools[k] for k in sorted(pools)]
    if len(ordered) != 1000 or any(set(p) != set(METHODS) for p in ordered):
        raise SystemExit("Expected exactly 1,000 paired pools and four methods per pool.")

    rng = random.Random(args.seed)
    print(f"pools={len(ordered)} methods={','.join(METHODS)} seed={args.seed} resamples={args.resamples}")
    for method in METHODS:
        rate = sum(p[method] for p in ordered) / len(ordered) * 100
        print(f"rate,{method},{rate:.3f}%")

    for baseline in ("point_estimate", "uniform_margin", "qubo_only"):
        diffs = [p["cb_pfr"] - p[baseline] for p in ordered]
        cb_wins = sum(d == 1 for d in diffs)
        base_wins = sum(d == -1 for d in diffs)
        boots = []
        for _ in range(args.resamples):
            boots.append(sum(diffs[rng.randrange(len(diffs))] for _ in diffs) / len(diffs) * 100)
        print(
            f"paired,cb_pfr-minus-{baseline},"
            f"{sum(diffs)/len(diffs)*100:.3f} pp,"
            f"percentile95=[{quantile(boots,0.025):.3f},{quantile(boots,0.975):.3f}],"
            f"discordant={cb_wins}:{base_wins},"
            f"exact_two_sided_p={exact_sign_p((cb_wins,base_wins)):.12g}"
        )

if __name__ == "__main__":
    main()
