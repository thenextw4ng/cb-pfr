# Reproducibility

## Status

The frozen 1,000-trial synthetic benchmark has now been independently reproduced from the released source and configuration in a clean working environment.

Protocol:
- 1,000 trials
- 12 candidates per trial
- seed = 20261005 + trial_index
- four methods receive the identical synthetic observation pool
- known synthetic normal observation model
- 0.98 upper feasibility limit
- candidate-specific standard errors of 0.004 or 0.010
- uniform comparison margin 0.008

## Exact reproduction check

The regenerated trial-level selections, latent truth values, feasibility flags, observed estimates, and reported standard errors match the preserved archival result artifact for all 4,000 method/trial rows.

Aggregate rates:
- QUBO-only: 0.857
- point estimate: 0.933
- CB-PFR: 0.976
- uniform margin: 0.966

This establishes software/protocol reproducibility for the synthetic mathematical experiment. It does not establish physical validation.

## Clean run

    python -m venv .venv
    . .venv/bin/activate
    pip install -e .
    PYTHONPATH=src python scripts/run_reduced_synthetic_calibration.py --results-dir results/reproduced_run

The runner refuses to overwrite an existing nonempty results directory.

## Audit

per_seed_results.csv is the archived 4,000-row result artifact. results/recorded_results_audit.json contains the statistical audit of that artifact.

The exact reproduced output agrees on the substantive experiment columns. Metadata columns added during release auditing are provenance annotations and do not change the experiment.

## What this does not prove

A successful rerun verifies the deterministic software protocol under the declared synthetic data-generating process. It does not calibrate uncertainty for MC/DC/OpenMC, establish physical relevance, or demonstrate universal superiority.
