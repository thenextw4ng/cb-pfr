#!/usr/bin/env python3
"""Descriptive post-hoc audit of OpenMC HDF5 batch traces; never certifies convergence."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import h5py
import numpy as np


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def summarize(values: np.ndarray) -> dict:
    if values.size == 0 or not np.isfinite(values).all():
        raise ValueError("trace must be non-empty and finite")
    quarter = max(1, values.size // 4)
    half = max(1, values.size // 2)
    slope = float(np.polyfit(np.arange(values.size, dtype=float), values, 1)[0] * 1000) if values.size > 1 else 0.0
    first_half = values[:half].mean()
    last_half = values[half:].mean() if values[half:].size else float(values[-1])
    return {
        "n": int(values.size),
        "mean": float(values.mean()),
        "min": float(values.min()),
        "max": float(values.max()),
        "first_quarter_mean": float(values[:quarter].mean()),
        "last_quarter_mean": float(values[-quarter:].mean()),
        "last_minus_first_quarter_mean": float(values[-quarter:].mean() - values[:quarter].mean()),
        "first_half_mean": float(first_half),
        "last_half_mean": float(last_half),
        "last_minus_first_half_mean": float(last_half - first_half),
        "ols_slope_per_1000_batches": slope,
    }


def audit(path: Path) -> dict:
    with h5py.File(path, "r") as statepoint:
        n_batches = int(statepoint["n_batches"][()])
        inactive = int(statepoint["n_inactive"][()])
        seed = int(statepoint["seed"][()]) if "seed" in statepoint else None
        k = np.asarray(statepoint["k_generation"], dtype=float).reshape(-1)
        entropy = np.asarray(statepoint["entropy"], dtype=float).reshape(-1) if "entropy" in statepoint else np.array([])
    if n_batches != k.size or (entropy.size and n_batches != entropy.size):
        raise ValueError(f"{path}: HDF5 metadata/trace length mismatch")
    if not 0 <= inactive < n_batches:
        raise ValueError(f"{path}: invalid inactive batch count {inactive}")
    if not np.isfinite(k).all() or (entropy.size and not np.isfinite(entropy).all()):
        raise ValueError(f"{path}: non-finite trace")

    inactive_k, active_k = k[:inactive], k[inactive:]
    inactive_h = entropy[:inactive] if entropy.size else entropy
    active_h = entropy[inactive:] if entropy.size else entropy
    window = min(100, inactive_h.size)
    return {
        "statepoint": str(path),
        "statepoint_sha256": sha256(path),
        "seed": seed,
        "n_batches": n_batches,
        "n_inactive": inactive,
        "n_active": n_batches - inactive,
        "inactive_k_generation": summarize(inactive_k) if inactive_k.size else None,
        "inactive_entropy": summarize(inactive_h) if inactive_h.size else None,
        "inactive_entropy_first_window_mean": float(inactive_h[:window].mean()) if window else None,
        "inactive_entropy_last_window_mean": float(inactive_h[-window:].mean()) if window else None,
        "inactive_entropy_first_to_last_window_relative_change_pct": (
            float(100 * (inactive_h[-window:].mean() - inactive_h[:window].mean()) / inactive_h.mean())
            if window and inactive_h.mean() else None
        ),
        "active_k_generation": summarize(active_k),
        "active_entropy": summarize(active_h) if active_h.size else None,
        "status": "DIAGNOSTIC_REVIEW_REQUIRED",
        "automatic_source_convergence_pass": False,
        "interpretation": "Descriptive HDF5 trace audit only; review inactive source entropy and active traces against declared criteria.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--statepoint", type=Path, action="append", required=True,
                        help="Statepoint HDF5 path; repeat for each independent run")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        parser.error(f"refusing to overwrite existing output: {args.out}")
    reports = [audit(path) for path in args.statepoint]
    output = {
        "schema_version": "1.0",
        "status": "DESCRIPTIVE_HDF5_BATCH_TRACE_AUDIT_COMPLETE",
        "run_count": len(reports),
        "automatic_source_convergence_pass": False,
        "runs": reports,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(output, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": output["status"], "run_count": len(reports), "out": str(args.out)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
