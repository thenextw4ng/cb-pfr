# Confirmatory synthetic CB-PFR comparison — execution report

**Execution:** 11 October 2026  
**Protocol:** `reports/CB_PFR_RS_SYNTHETIC_CONFIRMATORY_PREREGISTRATION_2026-10-11.md`, version 1.1  
**Workflow:** [GitHub Actions run 38122708676](https://github.com/thenextw4ng/cb-pfr/actions/runs/38122708676)  
**Artifact:** `cbpfr-rs-synthetic-confirmatory` (raw trial records, JSON summary, execution log; 90-day retention)  
**Commit:** [092c44f](https://github.com/thenextw4ng/cb-pfr/commit/092c44f32f878e6d55cd92a7131ba1098ce4a778)  
**Status:** `EXECUTED_SYNTHETIC_ONLY_NOT_PHYSICAL_VALIDATION`

## Locked experiment

- Four prespecified scenarios × 10,000 independent candidate pools per scenario = 40,000 pools.
- 12 candidates per pool; seed 20261013 with documented scenario offsets.
- Compared CB-PFR-style uncertainty screen against fixed-pool point-estimate selection and a uniform-margin screen.
- Primary outcome: whether the selected candidate's latent response meets the synthetic feasibility threshold.
- Paired pool-level bootstrap 95% confidence intervals and exact McNemar tests; Holm correction for the two pooled primary comparisons.
- The run used Python 3.12.15 and NumPy 2.5.4.

The baseline named `point_estimate_rs` is **not** an adaptive sequential R&S algorithm. It is point-estimate selection from the same fixed candidate pool.

## Primary pooled result

| Comparator | CB-PFR feasibility-rate difference | Paired bootstrap 95% CI | Holm-adjusted McNemar p | Preregistered rule |
|---|---:|---:|---:|---|
| Point-estimate selection | +0.4875 percentage points | +0.3725 to +0.6000 pp | 1.165 × 10⁻¹⁶ | **Fail** |
| Uniform margin | +0.4875 percentage points | +0.3700 to +0.6025 pp | 1.165 × 10⁻¹⁶ | **Fail** |

The effects are statistically distinguishable from zero in this stylized synthetic mixture, but the absolute gain is below the prespecified minimum of **2 percentage points**. Therefore the locked decision rule returns:

**`prespecified_synthetic_advantage_supported = false`.**

Do not report this as confirmation that CB-PFR is superior. The correct interpretation is that the confirmatory test detected a small pooled synthetic improvement, but it did not meet the prespecified practical-effect threshold. Equal-sized scenario pooling also masks heterogeneity, so the scenario-specific results matter.

## Scenario-specific selected true-feasibility rates

| Scenario | Point estimate | CB-PFR | Uniform margin | Interpretation |
|---|---:|---:|---:|---|
| Calibrated heteroscedastic | 93.84% | 95.47% | 93.84% | CB-PFR +1.63 pp versus both baselines |
| Calibrated homoscedastic | 95.57% | 95.57% | 95.57% | No selection-feasibility gain |
| Underreported uncertainty (reported SE ×0.5) | 93.56% | 93.88% | 93.56% | Only +0.32 pp; uncertainty underreporting also reduces lower-bound coverage |
| Shifted / near-threshold | 95.22% | 95.22% | 95.22% | No selection-feasibility gain |

## Calibration stress result

Empirical coverage of the one-sided lower bound `estimate − 1.96 × reported_se` was:

- Calibrated heteroscedastic: 97.5225%.
- Calibrated homoscedastic: 97.5133%.
- Underreported uncertainty: 83.5775%.
- Shifted / near-threshold: 73.4233%.

The first two are close to the nominal 97.5% one-sided coverage under the calibrated Gaussian synthetic assumptions. The stress cases show that the bound does not retain that nominal coverage when uncertainty is underreported or observations are systematically shifted. This is a synthetic calibration diagnostic, not a guarantee for OpenMC outputs.

## Reproducibility fingerprints

- Raw CSV SHA-256: `b661bcfc7cda9a5a013948da45cb35bdc6a17d9c49d6f1c99063d6d5df81a0a1`
- Script SHA-256: `5f25a52427a693ab0fbc895c76ca41b58670eef361c2a3e3d6c8abf2afa44a06`
- Workflow artifact SHA-256: `16a8d487a0e614d707bf76c8da16cd4701f80a96a24199309e73aecd85270f20`

## Scientific conclusion

The locked synthetic confirmation **does not pass** its prespecified advantage rule. CB-PFR improves selected latent-feasibility rate by about 0.49 percentage points when pooling all four scenarios, below the required 2 pp, with no gain in two scenarios. It also confirms a meaningful failure mode: uncertainty-aware screening cannot recover nominal lower-bound coverage when the supplied uncertainty is miscalibrated or the observations are shifted.

This result is useful and should be reported honestly. It does not validate physical reactor ranking, establish general superiority, validate a QUBO-to-material mapping, or demonstrate quantum advantage. The next physical claim still requires a predeclared, higher-budget OpenMC candidate comparison with common budgets, justified criteria, repeated independent runs, and baseline comparison.
