# Results

This directory contains the checked-in aggregate results and audit metadata for the CB-PFR synthetic benchmark.

## Available in this repository

- `main_results.csv`: four-method aggregate summary.
- `recorded_results_audit.json`: statistical audit metadata for the preserved recorded outputs.
- `reduced_synthetic_benchmark/` is the default output location for a fresh run; the runner writes trial-level selections, aggregate tables, coverage information, and a protocol snapshot there when executed.

## Reproduction versus archival artifacts

The released source and configuration include a 1,000-trial synthetic benchmark runner. The latest repository CI workflow checks the reproducibility path and the recorded aggregate rates. The original archival `per_seed_results.csv` (4,000 method/trial rows) is **not currently checked into this public repository**; it remains tracked for synchronization in Issue #9.

Therefore, readers can run the released benchmark and inspect its generated output, but cannot independently compare every generated row with the original archival CSV from this repository alone until that archival file is added.

## Interpretation

All results are conditional on the declared synthetic data-generating process. They are software/protocol evidence, not physical validation, reactor-safety evidence, or proof of universal superiority.
