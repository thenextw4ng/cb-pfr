# C5G7 same-pool CB-PFR versus point-estimate synchronization audit — 2026-10-11

**Decision: NO DEMONSTRATED CB-PFR ADVANTAGE IN THE CURRENT C5G7 SMOKE DATA.** This is a re-analysis of committed data, not a new OpenMC transport run.

## Source and integrity

- Run-level source: `results/c5g7_corrected_group_repeatability_smoke_2026-10-11/run_level_fission_objective.csv`
- Summary source: `results/c5g7_corrected_group_repeatability_smoke_2026-10-11/fission_objective_repeatability_summary.csv`
- Parsed run-level rows: 18, six layouts, three independent seed labels per layout.
- All runs carry the same recorded MGXS hash and `group_structure_audit=PASS` in the run-level CSV.
- Budget is exploratory: 100 batches, 10 inactive, 1,000 particles per batch, as documented in the physical-effectiveness gate report.

## Recomputed same-pool ranking

The audit recomputed each layout's arithmetic mean peaking proxy and sample standard deviation across its three runs. The illustrative risk-adjusted score is `mean_peaking + 1.0 × between-seed sample SD`, matching the report's configured risk weight. Lower is better.

| Layout | n | Mean peaking | Between-seed SD | Mean + SD | Point-estimate rank | Risk-adjusted rank |
|---|---:|---:|---:|---:|---:|---:|
| MUMU | 3 | 1.296265 | 0.022605 | 1.318870 | 1 | 1 |
| MUUM | 3 | 1.310279 | 0.022338 | 1.332618 | 2 | 2 |
| MMUU | 3 | 1.327285 | 0.011865 | 1.339150 | 3 | 3 |
| UUMM | 3 | 1.825391 | 0.024419 | 1.849809 | 4 | 4 |
| UMUM | 3 | 1.855918 | 0.046896 | 1.902814 | 5 | 5 |
| UMMU | 3 | 1.886113 | 0.028995 | 1.915108 | 6 | 6 |

**Finding:** point-estimate and risk-adjusted ranking order are exactly identical (Spearman rank agreement = 1 for these six candidates). CB-PFR does not change the selected candidate: MUMU wins under both rules. This is not evidence that uncertainty-aware ranking is useless generally; it means this particular candidate pool and small smoke dataset do not demonstrate an incremental selection benefit.

## Why this is not yet a valid physical-effectiveness test

1. The gate report says all six candidates pass the illustrative conservative feasibility screen. Therefore the feasibility gates do not discriminate among candidates.
2. The peaking proxy is a relative assembly fission-rate shape statistic, not absolute power or a safety metric; the acceptance limits are illustrative rather than authoritative reactor acceptance criteria.
3. Three low-budget runs per layout are insufficient to characterize the tail/uncertainty of the peaking metric robustly. The reported between-seed SD is descriptive and is not automatically a calibrated confidence bound.
4. The one-hot QUBO in the integration smoke was constructed from declared candidate scores. Agreement with its output is an integration-consistency check, not an independent comparison against a separately specified QUBO optimizer.
5. The legacy QUBO states fresh/once-burned/twice-burned do not have a defensible mapping to these separate 2×2 UO2/MOX layouts. The C5G7 experiment is therefore an explicit reformulation, not validation of the legacy QUBO-to-physics mapping.

## Decision and next test

- Do not claim physical effectiveness or superiority from this dataset.
- Do not launch a high-budget transport run merely to seek a positive result.
- Next, freeze an authoritative physical objective/acceptance rule and candidate-to-model mapping; then compare all four methods on identical candidate pools and equal evaluation budgets, with independent confirmation seeds and reference-evaluated outcomes.
- Keep model validation (whether OpenMC matches applicable reference evidence) separate from method validation (whether CB-PFR selects better candidates than baselines).

## Claim that the current evidence supports

“CB-PFR was integrated with an exploratory C5G7 2×2 UO2/MOX candidate study. In the current 18-run smoke dataset, the illustrative mean-plus-standard-deviation ranking selected the same layout as point-estimate ranking; no incremental CB-PFR selection advantage was observed. Physical effectiveness remains unestablished.”
