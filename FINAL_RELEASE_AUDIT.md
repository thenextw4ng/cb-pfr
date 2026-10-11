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
- Six low-budget C5G7 assembly-placement smoke runs with candidate IDs, explicit seeds, statepoint/input hashes, and summary CSV/JSON under `results/c5g7_layout_smoke_2026-10-10/`.
- An 18-run, three-round C5G7 repeatability smoke study with raw-HDF5 audit results, per-run statepoint hashes, between-run variability, and descriptive ranking stability under `results/c5g7_repeatability_smoke_2026-10-11/`.
- A corrected 18-run normalized-MGXS repeatability study under `results/c5g7_repeatability_normalized_2026-10-11/`; all runs use the production-identical MGXS SHA-256 and all 336 raw-HDF5 checks pass.
- Production-versus-regenerated canonical input comparison showing geometry/tally/plot XML identity, material-definition identity after normalizing the local cross-section path, and byte-identical MGXS. See `reports/c5g7_input_provenance_comparison_2026-10-11.md`.
- Six-layout assembly-integrated fission-rate proxy smoke outputs under `results/c5g7_assembly_fission_proxy_smoke_2026-10-11.csv`; these are normalized fission-rate metrics, not absolute power.
- Machine-readable fail-closed validation gates and canonical convergence workflow under `scripts/analyze_c5g7_canonical_convergence.py` and `config/benchmarks/c5g7_validation_protocol.json`.
- PR #19 merged; CI passed on Python 3.10, 3.11, and 3.12 at the merge commit.
- Software citation metadata in `CITATION.cff` and `.zenodo.json`.

## Evidence taxonomy

- **Synthetic software/protocol evidence:** reported 1,000-trial study under a known synthetic normal observation model.
- **Archived data:** `results/per_seed_results.csv`, retained for inspection and row-level comparison.
- **Independent computational rerun:** the released source and frozen configuration were executed to regenerate the benchmark; substantive trial-level fields and aggregate rates matched the archival output. This is not an external third-party replication.
- **Recorded transport execution evidence:** the audited production C5G7 statepoint plus six low-budget assembly-placement smoke runs. The smoke runs are exploratory and not benchmark-grade; neither establishes CB-PFR physical validation.
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

The production statepoint audit, normalized repeated-seed smoke study, input-provenance comparison, and fission-rate proxy outputs are execution/data-extraction evidence. A canonical high-budget numerical screen and a six-layout intermediate-budget screen are running in GitHub Actions; their results must be added after completion. None of these artifacts establishes a validated QUBO-to-physics mapping, official benchmark acceptance, benchmark-grade spatial power comparison, a validated CB-PFR transport workflow, or reactor-safety evidence.

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


## Follow-up evidence audit — 2026-10-11

The five-minute corrected-group C5G7 quick-check completed at [Actions run 38112118549](https://github.com/thenextw4ng/cb-pfr/actions/runs/38112118549), commit `1907b2babb250923a73e06f67a51842d561d20e3`. It ran one new OpenMC 0.16.0 transport case and passed 22/22 raw-HDF5 checks. The actual output was (k_{eff}=1.1728029349321403pm0.019472323678449033), with assembly-integrated fission-rate peaking factor 1.942932842839654. Settings were 20 total batches, 5 inactive, 100 particles per batch; this is low-statistics execution evidence only.

The published reference in Song et al. (2020), Table 1, reports (k_{eff}=1.18655pm9.5) pcm and maximum normalized **pin** power 2.498. The local 1.94293 metric is a ratio of assembly-integrated fission tallies and is not comparable to maximum pin power. The numerical (k_{eff}) screen is recorded in `results/benchmark_comparison.csv`; model-identity review and convergence remain blocked. See `docs/IMPLEMENTATION_AUDIT.md`, `docs/C5G7_MODEL_AUDIT.md`, and `docs/INDEPENDENT_VALIDATION.md`.

A new independent-replicate aggregator and metric-aware reference comparator have been added with automated tests. The aggregator is a code path, not a completed multi-seed uncertainty result; the quick-check still contains only one statepoint. Experimental physical validation remains **not established**.
