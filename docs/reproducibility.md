# Reproducibility

## Status

The released source and configuration include a 1,000-trial synthetic benchmark runner. GitHub Actions has previously completed successfully; check the repository's Actions page for the latest run status. The archived trial-level output is also checked into the repository as `results/per_seed_results.csv`.

The archive contains 4,000 method/trial rows (1,000 trials × 4 methods). It supports direct inspection and row-level auditing. Do not assume that a newly generated run is an exact reproduction until you compare the outputs and account for the software environment and protocol.

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

## Archival audit

The archived file `results/per_seed_results.csv` records the original trial-level results. Its SHA-256 is:

`f7fb629fa182778645c41dcbc20f063599b41e09d428ea8204d4af10855e2133`

A prior audit reports that an independent rerun matched all 4,000 substantive method/trial rows. To reproduce that audit, compare the fresh output against the archive using the same row keys and documented substantive columns; do not compare generated timestamps or non-substantive metadata as if they were scientific outcomes.

## What this does not prove

A successful rerun verifies the software protocol under the declared synthetic data-generating process. It does not calibrate uncertainty for MC/DC/OpenMC, establish physical relevance, demonstrate universal superiority, or establish safety. The MC/DC C5G7 run is execution evidence only; no defensible mapping from the abstract QUBO labels to that benchmark has been established.
