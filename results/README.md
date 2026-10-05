# Results

This directory contains the aggregate results, audit metadata, and archived trial-level output for the CB-PFR synthetic benchmark.

## Available in this repository

- `main_results.csv`: four-method aggregate summary.
- `recorded_results_audit.json`: statistical audit metadata for the preserved recorded outputs.
- `per_seed_results.csv`: archival trial-level table with 4,000 method/trial rows (1,000 trials × 4 methods).
- A fresh run writes trial-level selections, aggregate tables, coverage information, and a protocol snapshot to the output directory specified by the user.

## Reproduction versus archival artifacts

The released source and configuration include a 1,000-trial synthetic benchmark runner. The preserved archival CSV is available for inspection and independent row-level comparison. A fresh run generates new outputs; exact agreement should only be claimed after checking the environment, protocol, seeds, and row-level comparison.

## Interpretation

All results are conditional on the declared synthetic data-generating process. They are software/protocol evidence, not physical validation, reactor-safety evidence, or proof of universal superiority.
