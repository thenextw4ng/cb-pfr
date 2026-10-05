# Release Audit

## Release status

CB-PFR is prepared as a transparent research/software prototype and methodological working paper. The public repository contains the source code, benchmark configuration, aggregate results, archival trial-level CSV, reproducibility/audit documentation, and software metadata. The methodological working paper is maintained as a separate publication artifact. Physical CB-PFR validation remains **not established**.

This audit describes the repository evidence boundary; it is not a claim of peer review, physical validation, or production readiness.

## Repository contents checked

- Core CB-PFR ranking implementation and abstract QUBO construction.
- Exact enumeration for the seven-position toy model.
- Automated tests and GitHub Actions workflow.
- Reduced 1,000-trial synthetic benchmark runner and configuration.
- Aggregate result table and statistical audit metadata.
- Archived `results/per_seed_results.csv` with 4,000 method/trial rows.
- Reproducibility, limitations, and physical-mapping documentation.
- Software citation metadata in `CITATION.cff` and `.zenodo.json`.

## Evidence taxonomy

- **Synthetic software/protocol evidence:** reported 1,000-trial study under a known synthetic normal observation model.
- **Archived data:** `results/per_seed_results.csv`, retained for inspection and row-level comparison.
- **Independent computational rerun:** the released source and frozen configuration were executed to regenerate the benchmark; substantive trial-level fields and aggregate rates matched the archival output. This is not an external third-party replication.
- **Recorded transport execution evidence:** MC/DC C5G7 benchmark run; this is not CB-PFR physical validation.
- **Physical CB-PFR validation:** not established.

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
- Final methodological working-paper PDF SHA-256 (publication artifact): `f9f5fa0aa34120e5708f29b578cf75d0a63b75660b271410a8cc2a6b9e5c3965`
- Final LaTeX source SHA-256 (publication workspace): `7f1481e343d2220f4ce9a47deb2a3dab034ebca006b9e1d420be057f1cc14940`

The paper checksum identifies the exact publication artifact prepared for the separate Zenodo preprint record.

## Remaining research gates

1. Publish the GitHub `v0.1.0` release and archive it through Zenodo.
2. Add the resulting software DOI to the publication record and paper citation section.
3. Conduct uncertainty calibration, sensitivity analysis, and pre-specified ablations.
4. Define and justify a defensible physical benchmark and category-to-material mapping.
5. Evaluate against relevant optimization/selection baselines using equal physical-evaluation budgets.
6. Obtain independent external runs and users.

## Release language

Appropriate description: **open research prototype with synthetic benchmark evidence and an explicit unresolved physical-validation boundary**.

Do not describe CB-PFR as physically validated, reactor-safe, peer-reviewed, or universally superior unless new evidence supports those claims.
