# Reproducibility

## Status

The released source and configuration include a 1,000-trial synthetic benchmark runner. The repository's latest GitHub Actions run completed successfully, and the workflow includes the synthetic reproducibility check. This supports software/protocol reproducibility under the declared synthetic data-generating process.

The original archival `per_seed_results.csv` (4,000 method/trial rows) is **not currently checked into this public repository**. As a result, the repository user can generate a fresh trial-level output but cannot compare every row to that original archival file using this repository alone.

## Protocol

- 1,000 trials
- 12 candidates per trial
- seed = 20261005 + trial_index
- four methods receive the identical synthetic observation pool
- known synthetic normal observation model
- 0.98 upper feasibility limit
- candidate-specific standard errors of 0.004 or 0.010
- uniform comparison margin 0.008

## Aggregate reference rates

- QUBO-only: 0.857
- point estimate: 0.933
- CB-PFR: 0.976
- uniform margin: 0.966

These are conditional synthetic benchmark rates, not physical outcomes.

## Clean run

    python -m venv .venv
    . .venv/bin/activate
    pip install -e .
    python scripts/run_reduced_synthetic_calibration.py --results-dir results/reproduced_run

Use a new, empty output directory. The runner refuses to overwrite a nonempty results directory. It writes trial-level selections, aggregate tables, coverage information, and a protocol snapshot.

## Archival audit boundary

`results/recorded_results_audit.json` contains a statistical audit of the recorded outputs. The original `per_seed_results.csv` is tracked in Issue #9 for synchronization; until it is committed or attached to a stable public archive, the exact archival row-by-row comparison cannot be independently performed from this repository alone.

## What this does not prove

A successful rerun verifies the software protocol under the declared synthetic data-generating process. It does not calibrate uncertainty for MC/DC/OpenMC, establish physical relevance, demonstrate universal superiority, or establish safety. The MC/DC C5G7 run is execution evidence only; no defensible mapping from the abstract QUBO labels to that benchmark has been established.
