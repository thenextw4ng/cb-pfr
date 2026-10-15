# C5G7 corrected entropy-mesh recheck — 15 October 2026

## Scope and decision

This report audits six completed, single-layout UMMU OpenMC reruns from GitHub Actions. The entropy mesh is 2D, 51×51, with bounds [-32.14, 32.14] in x and y. The declared core extent from the lattice construction is [-32.13, 32.13], so the mesh extends 0.01 length unit beyond the modeled core at each side. Each run has 7,000 batches and 10,000 particles per batch; the two protocols use 500 or 100 inactive batches.

**Mesh-warning subgate: PASS for these six executions.** Each run completed, a nonempty statepoint exists, the settings and statepoint seed agree, and all six OpenMC logs contain zero `Fission source site(s) outside of entropy box` warnings.

**Convergence / run-to-run reliability gate: NOT PASSED / NOT CERTIFIED.** Protocol B (100 inactive batches) still exhibits unusually low between-run dispersion relative to its within-run reported uncertainty. Protocol A (500 inactive batches) also has nontrivial first-to-last active-quartile k-generation shifts. The workflow intentionally records `convergence_certified=false`; this report preserves that status.

## Per-run statepoint audit

| Protocol | Seed | k-effective mean | Within-run SD (pcm) | Δk Q4−Q1 (pcm) | Δentropy Q4−Q1 | Entropy-mesh warnings | Entropy ACF lag 1 | k-generation ACF lag 1 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| A: 500 inactive | 720000 | 1.18631823405 | 9.419 | +42.06 | -0.000068 | 0 | 0.688 | 0.016 |
| A: 500 inactive | 730000 | 1.18654500038 | 9.698 | +65.05 | -0.001947 | 0 | 0.722 | 0.026 |
| A: 500 inactive | 740000 | 1.18661640096 | 9.617 | +23.99 | -0.001035 | 0 | 0.710 | 0.018 |
| B: 100 inactive | 720000 | 1.18646840890 | 9.394 | +23.49 | -0.000659 | 0 | 0.711 | 0.007 |
| B: 100 inactive | 730000 | 1.18646989491 | 9.463 | -16.09 | +0.000443 | 0 | 0.717 | 0.005 |
| B: 100 inactive | 740000 | 1.18648242266 | 9.481 | -7.91 | +0.000431 | 0 | 0.705 | 0.025 |

Quartiles are calculated from the exact `k_generation` and `entropy` arrays in each statepoint, using active batches only. ACF is calculated on active-batch traces.

## Protocol summaries

### Protocol A — 500 inactive batches

- Mean of three run-level k-effective estimates: `1.18649321180`; difference from the published reference 1.18655 is `-5.68 pcm` (descriptive, not a validation test).
- Between-run sample SD: `15.568 pcm`; pooled within-run SD: `9.579 pcm`; ratio: `1.6253`.
- First-to-last active-quartile k-generation shifts: +42.06, +65.05, and +23.99 pcm.
- First-to-last active-quartile source-entropy shifts: -0.000068, -0.001947, and -0.001035.
- Mean lag-1 ACF: k-generation `0.020`, entropy `0.707`. The first-lag entropy correlation is high; this makes an independence assumption for consecutive entropy batches inappropriate.

### Protocol B — 100 inactive batches

- Mean of three run-level k-effective estimates: `1.18647357549`; difference from the published reference 1.18655 is `-7.64 pcm` (descriptive, not a validation test).
- Between-run sample SD: `0.770 pcm`; pooled within-run SD: `9.446 pcm`; ratio: `0.0815`.
- First-to-last active-quartile k-generation shifts: +23.49, -16.09, and -7.91 pcm.
- Corrected first-to-last active-quartile source-entropy shifts: -0.000659, +0.000443, and +0.000431. These replace the old entropy diagnostics calculated while the source fell outside the mesh.
- Mean lag-1 ACF: k-generation `0.012`, entropy `0.711`. Source entropy remains strongly autocorrelated at lag 1.

## Interpretation and disposition

1. **Mesh warnings are resolved for these six reruns.** The mesh extends 0.01 length unit beyond the designed core boundary ±32.13, and the logs have zero source-outside-mesh warnings. This proves warning-free execution for these runs; it is not a formal proof of all material coverage and does not certify source convergence.
2. **The entropy diagnostic is now interpretable for Protocol B.** Its corrected entropy quartile shifts are close to zero, unlike the old warning-contaminated values around -0.475 to -1.456. Do not pool the old and corrected-mesh entropy diagnostics as though they were measurements from the same valid mesh.
3. **The transport result is unchanged at the displayed precision.** The corrected-mesh runs use the same six seed/protocol cells as the archived analysis. Their k-effective means reproduce the archived run-level means; this is a diagnostic re-execution, not six new independent seeds.
4. **Protocol B's under-dispersion remains the critical blocker.** Its between-run SD is 0.770 pcm against pooled within-run SD 9.446 pcm. The seed values in settings and statepoints are distinct, and statepoint/source-bank hashes differ, but hash uniqueness alone does not prove statistical independence or explain the low dispersion.
5. **Protocol A is not certified converged either.** Its active-quartile k-generation shifts span +24.0 to +65.1 pcm. The lag-1 k-generation autocorrelation is small, but no prospective numerical convergence tolerance or dependence-aware criterion was frozen before these runs.
6. A follow-up extension has been queued with seven additional seed values per protocol, bringing the planned total to ten seeds per protocol. Its results must be analysed separately when completed. Until then, the mesh-warning subgate passes, but the convergence / run-to-run reliability gate stays open.

## Reproducibility and evidence boundary

- Audited: 6/6 completed cases; 6/6 statepoints nonempty; 6/6 settings seeds agree with statepoint seed; total source-outside-mesh warnings: 0.
- The accompanying CSV records the statepoint SHA256, source-bank hash, geometry/MGXS hashes, mesh settings, exact statepoint diagnostics, and the explicit `convergence_certified=false` flag.
- This report does not claim physical-model validation, benchmark acceptance, calibrated uncertainty coverage, fuel-layout optimality, or certification of source convergence.
