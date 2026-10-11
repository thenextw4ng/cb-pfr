# CB-PFR physical-effectiveness gate: C5G7 repeated-run evidence

**Decision: PHYSICAL_EFFECTIVENESS_NOT_ESTABLISHED.** This report analyzes the committed corrected-group C5G7 smoke data. It does not assert a new simulation run.

## Data provenance and scope

- Input summary: `results/c5g7_corrected_group_repeatability_smoke_2026-10-11/fission_objective_repeatability_summary.csv`
- Run-level data: `results/c5g7_corrected_group_repeatability_smoke_2026-10-11/run_level_fission_objective.csv`
- 6 UO2/MOX layouts × 3 independent seeds = 18 OpenMC statepoints.
- Common smoke budget: 100 batches, 10 inactive, 1,000 particles/batch.
- The recorded audit reports the standard C5G7 group structure and one shared MGXS hash across these runs.
- Independent spatial-mapping audit status: `STRUCTURAL_MAPPING_CHECK_PASS; PHYSICAL_VALIDATION_NOT_ESTABLISHED`.

These are exploratory smoke runs. They are not benchmark-grade convergence evidence, and the six-layout 2×2 UO2/MOX design is a separate reformulation rather than a mapping of the legacy fresh/once-burned/twice-burned QUBO.

## Observed descriptive results

| Layout | Mean k-effective | Between-seed SD(k) | Mean fission-rate peaking proxy | Between-seed SD(peaking) |
|---|---:|---:|---:|---:|
| MMUU | 1.145413 | 0.003036 | 1.327285 | 0.011865 |
| MUMU | 1.144825 | 0.002170 | 1.296265 | 0.022604 |
| MUUM | 1.158474 | 0.002096 | 1.310279 | 0.022338 |
| UMMU | 1.186103 | 0.003863 | 1.886113 | 0.028995 |
| UMUM | 1.207894 | 0.002188 | 1.855918 | 0.046896 |
| UUMM | 1.205115 | 0.002012 | 1.825391 | 0.024418 |

The reported peaking quantity is the maximum assembly-integrated fission-rate proxy divided by its mean across the four fuel assemblies. It is a relative-shape proxy, not absolute power and not a safety metric.

## Gate A — canonical C5G7 reference check

The project's recorded canonical reference is (k_\mathrm{eff}=1.18655) with stated reference standard uncertainty 0.000095. The UMMU smoke mean is 1.186103, a difference of about −44.7 pcm. However:

- between-seed standard deviation is 0.003863, approximately 386 pcm;
- the per-run Monte Carlo standard deviations are about 0.0024–0.0027 (roughly 240–270 pcm), far above the project's provisional 10-pcm single-run screen;
- only three low-budget seeds are available;
- independent model-identity review and a benchmark-compatible spatial reference comparison remain open.

Therefore, proximity of the mean (k_\mathrm{eff}) to the published reference is not a benchmark pass. The uncertainty is much larger than the reference uncertainty, and the spatial/identity gates are not satisfied.

## Gate B — does CB-PFR show physical selection benefit?

Not yet. In the archived integration smoke, all six candidates passed illustrative screening limits (not benchmark-authoritative constraints). The selector returned MUMU. The descriptive mean fission-peaking proxy for MUMU is the lowest among the six candidates, but its between-seed SD is 0.0226 with only three replicates; the difference from MUUM (1.3103 mean, 0.0223 SD) is small relative to run-to-run variability. No uncertainty propagation to the peaking-factor estimate or calibrated physical-feasibility model has been established.

The integration smoke does not demonstrate that CB-PFR outperforms point-estimate ranking, QUBO-only selection, a uniform-margin baseline, or a random selector on physical outcomes. In particular, because every candidate passed the illustrative screen, this run does not test whether CB-PFR correctly rejects physically infeasible candidates.


### Same-pool ranking sanity check

Under the integration smoke's illustrative settings, all six layouts pass the conservative screen, so the feasibility indicator and aggregate constraint violation do not separate them. With the configured risk weight of 1.0, the ranking score is mean peaking proxy plus between-seed SD:

| Layout | Point estimate (mean peaking) | Risk-adjusted descriptive score | Rank by point estimate | Rank by risk-adjusted score |
|---|---:|---:|---:|---:|
| MUMU | 1.296265 | 1.318870 | 1 | 1 |
| MUUM | 1.310279 | 1.332618 | 2 | 2 |
| MMUU | 1.327285 | 1.339150 | 3 | 3 |
| UUMM | 1.825391 | 1.849809 | 4 | 4 |
| UMUM | 1.855918 | 1.902814 | 5 | 5 |
| UMMU | 1.886113 | 1.915108 | 6 | 6 |

The risk adjustment does not change the winner or ranking order in this tiny smoke dataset. Thus this dataset provides **no observed evidence of a CB-PFR selection advantage over point-estimate ranking**. The one-hot QUBO in the smoke is constructed from the declared CB-PFR candidate scores, so agreement between that QUBO and CB-PFR is an implementation-consistency check, not an independent solver-baseline comparison. Uniform-margin ranking also cannot meaningfully distinguish candidates when the same margin is applied and all candidates pass. A proper treatment-effect study remains required.

## Required work to close the gate

1. **Canonical model verification:** raise the independent-run budget until the predeclared (k_\mathrm{eff}) uncertainty screen is met; verify model identity, source configuration, energy-group structure, material assignments, and benchmark-compatible spatial results.
2. **Observable validation:** audit the 51×51 mesh-to-assembly integration and propagate raw tally covariance into the peaking proxy; distinguish within-run Monte Carlo error from between-seed variation.
3. **Physical acceptance constraints:** define design-specific, source-supported constraints before looking at candidate rankings. Do not reuse illustrative (k_\mathrm{eff}) bands as safety criteria.
4. **Fair selection experiment:** use one frozen candidate pool and identical physics-evaluation budgets for QUBO-only, point estimate, CB-PFR, uniform margin, and random baselines. Repeat enough independent seeds to quantify selection uncertainty.
5. **Effectiveness endpoint:** predeclare an outcome such as rate of selecting candidates that pass independently evaluated constraints, or regret against the best feasible candidate, and report uncertainty intervals.
6. **Keep evidence tracks separate:** BEAVRS full-core experimental-map comparison and C5G7 four-position layout study validate different models and observables. Neither automatically validates the legacy QUBO material-state mapping.

## Allowed claim

> A corrected-group C5G7 software integration smoke test evaluated six UO2/MOX layouts over three seeds and exercised the CB-PFR plus one-hot QUBO selection path. The smoke data are descriptive only; benchmark-grade physics validation and physical ranking effectiveness remain unestablished.

## References

- C5G7 end-to-end evidence audit: `reports/C5G7_END_TO_END_EVIDENCE_AUDIT_2026-10-11.md`
- C5G7 spatial mapping audit: `reports/C5G7_SPATIAL_MAPPING_AUDIT_2026-10-11.md`
- Objective and acceptance protocol: `config/benchmarks/c5g7_objective_protocol.json`
- Selection smoke report: `reports/c5g7_cbpfr_selection_smoke_2026-10-11.md`
- BEAVRS experimental comparison protocol: `reports/BEAVRS_CYCLE1_EXPERIMENTAL_COMPARISON_PROTOCOL.md`
