#!/usr/bin/env python3
"""Descriptive trace diagnostics for OpenMC C5G7 statepoint files.

This tool intentionally does not declare convergence. It computes run-level
summaries that must be interpreted against a predeclared validation protocol.
Requires h5py, numpy, pandas, scipy.
"""
from __future__ import annotations
import argparse
import glob
import os
from pathlib import Path
import h5py
import numpy as np
import pandas as pd
from scipy import stats


def summarize(x: np.ndarray, block_size: int = 500) -> dict[str, float | int]:
    x = np.asarray(x, dtype=float)
    if x.ndim != 1 or len(x) < 4 or not np.isfinite(x).all():
        raise ValueError("Trace must be a finite 1-D array with at least four samples")
    t = np.arange(len(x), dtype=float)
    fit = stats.linregress(t, x)
    q = max(1, len(x) // 4)
    b = min(block_size, max(1, len(x) // 2))
    nblocks = len(x) // b
    block_means = np.array([x[i*b:(i+1)*b].mean() for i in range(nblocks)])
    lag1 = float(np.corrcoef(x[:-1], x[1:])[0, 1]) if np.std(x[:-1]) and np.std(x[1:]) else float("nan")
    return {
        "n_active": int(len(x)), "mean": float(x.mean()), "sd": float(x.std(ddof=1)),
        "slope_per_1000_batches": float(fit.slope * 1000), "slope_p_naive": float(fit.pvalue),
        "first_quartile_mean": float(x[:q].mean()), "last_quartile_mean": float(x[-q:].mean()),
        "first_last_quartile_shift": float(x[-q:].mean() - x[:q].mean()), "lag1_corr": lag1,
        "block_size": int(b), "n_blocks": int(nblocks),
        "block_mean_sd": float(block_means.std(ddof=1)) if nblocks > 1 else float("nan"),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("root", help="Directory containing extracted statepoint.7000.h5 files")
    ap.add_argument("--output", default="trace_diagnostics.csv", help="Output CSV path")
    ap.add_argument("--pattern", default="**/statepoint.7000.h5", help="Glob below root")
    args = ap.parse_args()
    paths = sorted(glob.glob(os.path.join(args.root, args.pattern), recursive=True))
    if not paths:
        ap.error(f"No statepoint files found under {args.root!r} with pattern {args.pattern!r}")
    rows = []
    for path in paths:
        run = next((part for part in Path(path).parts if part.startswith("c5g7-2x2-")), Path(path).parent.name)
        layout = run.removeprefix("c5g7-2x2-")
        with h5py.File(path, "r") as statepoint:
            inactive, batches = int(statepoint["n_inactive"][()]), int(statepoint["n_batches"][()])
            if inactive < 0 or inactive >= batches:
                raise ValueError(f"Invalid inactive/batch metadata in {path}: {inactive}/{batches}")
            entropy, k_generation = statepoint["entropy"][inactive:], statepoint["k_generation"][inactive:]
        row = {"run": run, "layout": layout, "n_batches": batches, "n_inactive": inactive}
        row.update({f"entropy_{k}": v for k, v in summarize(entropy).items()})
        row.update({f"kgen_{k}": v for k, v in summarize(k_generation).items()})
        rows.append(row)
    frame = pd.DataFrame(rows).sort_values(["layout", "run"])
    output = Path(args.output); output.parent.mkdir(parents=True, exist_ok=True); frame.to_csv(output, index=False)
    print(f"Analyzed {len(frame)} statepoints -> {output}")
    print("DIAGNOSTIC ONLY: no convergence pass/fail decision is produced.")
    for col in ("entropy_first_last_quartile_shift", "entropy_lag1_corr", "kgen_first_last_quartile_shift", "kgen_lag1_corr"):
        s = frame[col].dropna(); print(f"{col}: median={s.median():.8g}; max_abs={s.abs().max():.8g}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
