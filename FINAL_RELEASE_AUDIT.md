# Release Audit

## Release status

CB-PFR is released as a transparent research/software prototype and methodological working paper. The public repository includes the source, benchmark configuration, aggregate results, archival trial-level CSV, and working-paper PDF. Physical CB-PFR validation remains **not established**.

This audit describes the repository state and evidence boundary; it is not a claim of peer review, physical validation, or production readiness.

## Repository contents checked

- Core CB-PFR ranking implementation and abstract QUBO construction.
- Exact enumeration for the seven-position toy model.
- Automated tests and GitHub Actions workflow.
- Reduced 1,000-trial synthetic benchmark runner and configuration.
- Aggregate result table and statistical audit metadata.
- Archived `results/per_seed_results.csv` with 4,000 method/trial rows.
- `paper/CB-PFR_Methodological_Working_Paper.pdf`.
- Reproducibility, limitations, and physical-mapping documentation.

## Evidence taxonomy

- **Synthetic software/protocol evidence:** reported 1,000-trial study under a known synthetic normal observation model.
- **Archived data:** `results/per_seed_results.csv`, retained for inspection and row-level comparison.
- **Recorded transport execution evidence:** MC/DC C5G7 benchmark run; this is not CB-PFR physical validation.
- **Physical CB-PFR validation:** not established.

A prior audit reports that an independent rerun matched all 4,000 substantive method/trial rows. Readers should treat that as a documented audit result, not infer exact reproducibility merely because source and archived data are present. Check the protocol and row-level comparison before claiming reproduction.

## Recorded synthetic rates

| Method | Selected true-feasibility rate |
|---|---:|
| QUBO-only | 0.857 |
| Point estimate | 0.933 |
| CB-PFR | 0.976 |
| Uniform margin | 0.966 |

These rates are conditional on the synthetic data-generating process. They do not establish physical performance, universal superiority, or safety.

## Physical boundary

The seven-position QUBO uses abstract `fresh`, `once_burned`, and `twice_burned` labels. They are not mapped to C5G7 UO2/MOX material states. The mapping audit status remains:

`NO_DEFENSIBLE_MAPPING_FOUND`

The MC/DC C5G7 report is execution evidence only. It does not establish a validated QUBO-to-physics mapping, a validated CB-PFR transport workflow, or reactor-safety evidence.

## Artifact identity

- `results/per_seed_results.csv` SHA-256: `f7fb629fa182778645c41dcbc20f063599b41e09d428ea8204d4af10855e2133`
- `paper/CB-PFR_Methodological_Working_Paper.pdf` SHA-256 recorded before upload: `89e786d529ca3131e0182fcaad315dd4332491aa51253f936072cfda37bd5d96`
- `paper/source/main.tex` SHA-256 (source from audited workspace): `c0369fd420cba0b9c205503bee03841cd6bcdf082ba35838ad7ef7b90290a56f`

The local SHA-256 values above identify the audited source artifacts. The PDF checksum should be independently rechecked after download from GitHub if byte-for-byte identity is important.

## Remaining research gates

1. Re-run tests and benchmark in a clean environment and retain logs/checksums.
2. Reproduce the archived row-level comparison from documented commands and environment.
3. Conduct uncertainty calibration, sensitivity analysis, and pre-specified ablations.
4. Define and justify a defensible physical benchmark and category-to-material mapping.
5. Evaluate against relevant optimization/selection baselines using equal physical-evaluation budgets.
6. Obtain independent external runs and users.

## Release language

Appropriate description: **open research prototype with synthetic benchmark evidence and an explicit unresolved physical-validation boundary**.

Do not describe CB-PFR as physically validated, reactor-safe, peer-reviewed, or universally superior unless new evidence supports those claims.
