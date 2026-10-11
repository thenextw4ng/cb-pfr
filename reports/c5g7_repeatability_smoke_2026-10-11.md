# C5G7 repeated-seed smoke reliability analysis

## Status

**Completed: 18 OpenMC runs across six layouts and three explicit seed rounds.** Every round completed all six cases, and every raw-HDF5 audit passed. The run was performed with OpenMC 0.16.0 against upstream commit ba41bee54320ada0b4ac39a0dd2ca3c1d090a450.

- [Full repeated-run artifact](https://github.com/thenextw4ng/cb-pfr/actions/runs/38097472734)
- Artifact SHA-256: 8d7c0bdf4bee54ca429fe1a2fef78c5da3abbc173628b313aa257df88d2c99bd
- Settings: 100 batches, 10 inactive, 1,000 particles/batch, 1 thread; 90 active realizations per run.
- Seeds: 620000–620005, 630000–630005, and 640000–640005.
- Raw-HDF5 checks: 112/112 passed in each round; 336/336 check executions across the three rounds.
- All 18 seeds and statepoint hashes are unique; the same MGXS hash was used across all 18 runs.

## Candidate-level repeatability

| Candidate | Mean k_eff | Between-run sample SD | Pooled reported within-run SD | Between/within ratio | Rank range |
|---|---:|---:|---:|---:|---:|
| c5g7-2x2-MMUU | 1.14350016 | 0.00463111 | 0.00239977 | 1.930 | 1 |
| c5g7-2x2-MUMU | 1.14189995 | 0.00368754 | 0.00266893 | 1.382 | 1 |
| c5g7-2x2-MUUM | 1.15518399 | 0.00167428 | 0.00265975 | 0.629 | 0 |
| c5g7-2x2-UMMU | 1.18944503 | 0.00411599 | 0.00258361 | 1.593 | 0 |
| c5g7-2x2-UMUM | 1.20526283 | 0.00354565 | 0.00246122 | 1.441 | 1 |
| c5g7-2x2-UUMM | 1.20556426 | 0.00315624 | 0.00289253 | 1.091 | 1 |

Across the three rounds, the Spearman correlations between the descriptive k_eff rankings were 0.886, 0.943, and 0.943. Four of six layouts retained their exact rank across all rounds; two swapped adjacent positions.

The between-run sample SD exceeded the pooled within-run reported Monte Carlo SD for five of six layouts. With only three low-budget repetitions, this is a **warning signal to investigate**, not proof that OpenMC underestimates uncertainty. The estimates are noisy and do not account for model bias or nuclear-data uncertainty.

## MGXS byte-hash discrepancy

The earlier six-layout smoke artifact recorded MGXS byte SHA-256 170cc799f496e952465583bb078b2a88eae0f09886a821fd7ee8999d1eb93216. The repeated-run artifact records eab47265b45a9b350e5c8d28e60c2042fe32f84efe91d2636b731697ae0f8e64.

A structural comparison of those two HDF5 files found the same 63 datasets, the same dataset values/shapes/dtypes, and the same attributes across 95 HDF5 objects. Their canonical semantic fingerprint was identical: f6cb1ce367ab1113e72a2a1ebe2f313e95cce73c7fa5b95797256c956aa4871d. This indicates a byte-level HDF5 serialization difference rather than a difference in the stored MGXS content. The production baseline manifest records the first byte hash; the raw production MGXS file itself is not included in the evidence ZIP, so a fresh direct hash of that local file is still unavailable.

## Interpretation limits

1. These are exploratory smoke-budget runs, not benchmark-grade convergence results.
2. Three repetitions are too few for strong uncertainty calibration; between-run SD and rank correlations are descriptive.
3. The ranking is by k_eff only. It is not an optimization objective and does not recommend the lowest or highest k_eff layout.
4. The six assembly placements are a separate UO2/MOX design formulation, not a mapping of the legacy fresh/once_burned/twice_burned QUBO.
5. No benchmark acceptance, reactor-safety, or CB-PFR physical-validation claim follows from these runs.

## Reproducibility files

- repeatability_summary.csv — per-layout repeatability summary.
- run_level_results.csv — all 18 runs, seeds, statepoint hashes, settings hashes, and raw-HDF5 audit status.
- repeatability_analysis.json — machine-readable aggregate analysis.
- repeatability_manifest.json — workflow artifact identity, settings, and MGXS semantic comparison.
