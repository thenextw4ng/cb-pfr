# C5G7 CB-PFR/QUBO selection integration smoke — 11 October 2026

**Workflow:** https://github.com/thenextw4ng/cb-pfr/actions/runs/38116610735  
**Artifact:** c5g7-cbpfr-selection-smoke-38116610735  
**Status:** SELECTION_PIPELINE_PASS_PHYSICAL_VALIDATION_NOT_CERTIFIED

## What was actually executed

The GitHub Actions workflow consumed the archived corrected-seven-group C5G7 2×2 UO₂/MOX smoke dataset (six layouts × three independent seeds = 18 OpenMC statepoints), validated the group-structure audit and hash consistency, restored the archived compute settings (100 batches, 10 inactive, 1,000 particles/batch, one thread), and ran the existing CB-PFR + one-hot QUBO selection implementation.

- All 18 rows passed the corrected C5G7 energy-group audit.
- All 18 statepoint hashes were unique.
- One common MGXS hash was used across the dataset.
- All six layouts passed the illustrative screen configured for this integration test.
- The exact one-hot QUBO enumerated all \(2^6=64\) binary selector states and returned a unique one-hot minimizer.
- Selected candidate under these declared illustrative limits: **MUMU** (c5g7-2x2-MUMU).

## Illustrative screening parameters

| Parameter | Value |
|---|---:|
| \(k_\mathrm{eff}\) lower screen | 1.13 |
| \(k_\mathrm{eff}\) upper screen | 1.22 |
| Maximum fission-rate peaking proxy | 2.0 |
| Uncertainty multiplier | 2.0 |
| Risk weight on between-seed fission-peaking spread | 1.0 |
| Replicates per layout | 3 |
| Batches / inactive / particles per batch | 100 / 10 / 1,000 |

These limits were supplied solely to exercise the integration path. They are **not** official C5G7 acceptance criteria, reactor-safety limits, or benchmark-derived physical-feasibility requirements. The uncertainty multiplier is an operational heuristic, not a calibrated confidence interval.

## Interpretation boundary

This result establishes software-path consistency on an archived set of OpenMC calculations: a physical-data CSV passed the selection input audit, CB-PFR generated conservative-screen fields, and the one-hot QUBO selected the same candidate as the CB-PFR decision rule.

It does **not** establish:

- benchmark-grade convergence (the 100-batch / 1,000-particle runs are exploratory smoke runs);
- an official C5G7 benchmark pass for all six altered layouts;
- that MUMU is a physically optimal or safe reactor layout;
- that CB-PFR outperforms QUBO-only or other selection methods on physical data;
- a mapping from the legacy fresh/once-burned/twice-burned QUBO to UO₂/MOX;
- quantum-device execution or quantum advantage.

The next scientific gate remains the successful BEAVRS experimental-map run and its independent artifact audit, followed by higher-budget C5G7 candidate evaluations with predeclared, justified physical constraints and fair baseline comparisons.
