# Reproducibility

## Status

The released source and configuration include a 1,000-trial synthetic benchmark runner. The archived trial-level output is also checked into the repository as `results/per_seed_results.csv`.

The archive contains 4,000 method/trial rows (1,000 trials × 4 methods). The benchmark has already been **independently re-executed** from the released source and frozen configuration. All substantive trial-level fields in the regenerated output matched the archival CSV, and the four aggregate selected-feasibility rates matched exactly. This is an independent computational rerun, not an external third-party replication.

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

The released audit script recomputes the aggregate rates and paired comparisons from the recorded trial-level data. The independent computational rerun additionally regenerates the benchmark from source/configuration and checks substantive row-level equality against the archive.

## What this does not prove

A successful rerun verifies the software protocol under the declared synthetic data-generating process. It does not calibrate uncertainty for MC/DC/OpenMC, establish physical relevance, demonstrate universal superiority, or establish safety. The MC/DC C5G7 run is execution evidence only; no defensible mapping from the abstract QUBO labels to that benchmark has been established.
