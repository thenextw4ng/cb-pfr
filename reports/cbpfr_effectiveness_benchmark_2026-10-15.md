# CB-PFR fixed-budget synthetic effectiveness benchmark — 2026-10-15

**Workflow:** https://github.com/thenextw4ng/cb-pfr/actions/runs/38727150294  
**Commit:** `ad71cd6243a73cd4b851e7d32e68e24f7acb83ab`  
**Protocol:** `CBPFR-FIXED-BUDGET-SYNTHETIC-EFFECTIVENESS-2026-10-15`  
**Decision:** `NO_SYNTHETIC_SUPERIORITY_DEMONSTRATED`  
**Scope:** synthetic ranking-and-selection only. No physical validation claim.

## What was run

- 200 development pools to select the uniform-margin baseline; development data are excluded from confirmation.
- 1,000 confirmatory pools in each of six fixed regimes: 6,000 independent pools in total.
- 12 candidate evaluations per method per pool, with all four methods receiving the same candidate pool and same noisy observation table.
- Methods: QUBO-only, point-estimate, CB-PFR, and a uniform-margin baseline tuned only on development pools.
- The selected uniform margin was 0.020.
- Evaluator latent truth was kept in a separate data table and joined only after selections were made.
- Paired pool-level bootstrap intervals use 5,000 resamples.

The GitHub Actions workflow passed compile, execution, and output-integrity checks. The full raw CSV tables and protocol snapshot are preserved in artifact `CBPFR-fixed-budget-effectiveness-2026-10-15` from the workflow above (artifact retention is 30 days).

## Primary endpoint: latent feasible-selection rate

| Regime | QUBO-only | Point estimate | CB-PFR | Uniform margin |
|---|---:|---:|---:|---:|
| Calibrated low noise | 84.1% | 93.7% | 97.8% | 100.0% |
| Calibrated moderate noise | 83.1% | 91.7% | 97.1% | 98.7% |
| Calibrated high noise | 86.5% | 92.3% | 96.9% | 94.6% |
| Under-reported uncertainty (stress) | 84.9% | 92.2% | 95.8% | 98.3% |
| Contaminated heavy-tail noise (stress) | 84.7% | 92.1% | 96.3% | 96.9% |
| No truly feasible candidate (stress) | 0.0% | 0.0% | 0.0% | 0.0% |

Each rate uses 1,000 confirmatory pools. The exact Wilson 95% intervals and numerators/denominators are in `results/cbpfr_effectiveness_benchmark_2026-10-15_method_summary.csv`.

## Paired effect: CB-PFR minus baseline

The independent unit is the candidate pool. Pairwise differences are calculated from methods tested on the exact same pool, rather than treating candidates within a pool as independent replicates.

| Regime | Baseline | Difference in feasible-selection rate | Paired bootstrap 95% interval |
|---|---|---:|---:|
| Calibrated low noise | Point estimate | +4.1 pp | [+2.8, +5.4] pp |
| Calibrated low noise | Uniform margin | −2.2 pp | [−3.2, −1.3] pp |
| Calibrated moderate noise | Point estimate | +5.4 pp | [+3.9, +7.0] pp |
| Calibrated moderate noise | Uniform margin | −1.6 pp | [−2.7, −0.5] pp |
| Calibrated high noise | Point estimate | +4.6 pp | [+3.2, +6.0] pp |
| Calibrated high noise | Uniform margin | +2.3 pp | [+1.0, +3.7] pp |

CB-PFR outperformed the point-estimate baseline across all three calibrated regimes. However, it did **not** outperform the development-tuned uniform-margin baseline in the low- and moderate-noise regimes. The prespecified gate required the paired 95% interval to favor CB-PFR over both baselines in all three calibrated regimes, so the gate failed. Stress regimes do not rescue the primary gate.

## Interpretation and claim boundary

This run **does not establish general incremental selection superiority for CB-PFR**. It shows a reproducible implementation and comparison pipeline, with positive differences against point-estimate ranking, but also shows that a tuned conservative uniform margin can be better in some regimes. In this generator, under-reported uncertainty reduces CB-PFR's performance relative to the tuned uniform-margin baseline, and the no-feasible stress case correctly records a zero true feasible-selection rate for all methods while CB-PFR still has some false-feasible declarations.

These are synthetic, rule-generated responses—not OpenMC observations, C5G7 reference data, BEAVRS measurements, or reactor safety quantities. The benchmark cannot validate the CB-PFR physical interpretation, uncertainty calibration for Monte Carlo transport, or QUBO-to-material mapping.

## Reproduction

Use the branch `research/cbpfr-effectiveness-benchmark-20261015` and run:

```bash
python scripts/run_cbpfr_effectiveness_benchmark.py --outdir /tmp/cbpfr-effectiveness
```

Machine-readable outputs:
- `results/cbpfr_effectiveness_benchmark_2026-10-15_summary.json`
- `results/cbpfr_effectiveness_benchmark_2026-10-15_method_summary.csv`
- `results/cbpfr_effectiveness_benchmark_2026-10-15_paired_effects.csv`
- `results/cbpfr_effectiveness_benchmark_2026-10-15_development_margin_tuning.csv`

**Status:** method-level synthetic test completed; physical effectiveness remains unproven.
