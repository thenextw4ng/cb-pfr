# C5G7 six-layout higher-budget confirmation protocol — 2026-10-12

## Purpose

Increase the amount of reproducible physical-simulation evidence available before downstream CB-PFR analysis. This is a project-level repeated layout study using the pinned MIT-CRPG C5G7 source, not an official benchmark reproduction for every noncanonical layout and not a reactor-safety analysis.

## Design and compute budget

- Six assembly-level arrangements, each with exactly two MOX and two UO2 assemblies; five reflector positions remain fixed.
- Three independent seed rounds: 820000, 830000, and 840000. Candidate seed offsets are assigned deterministically by the study runner.
- Per run: 7,000 total batches, 500 inactive batches, 10,000 particles per batch, two OpenMC threads.
- Total runs: 18 (six layouts × three independent seed rounds).
- Nominal histories: 1,260,000,000; nominal active histories after inactive batches: 1,170,000,000.
- OpenMC 0.16.0, Python 3.12.
- Pinned upstream source commit: `ba41bee54320ada0b4ac39a0dd2ca3c1d090a450`.
- Audited seven-group boundaries: `[1e-5, 0.0635, 10, 100, 1000, 500000, 1000000, 20000000] eV`.

## Completed execution

- GitHub Actions run: [38229045726](https://github.com/thenextw4ng/cb-pfr/actions/runs/38229045726).
- Branch at execution: `feature/step05-scientific-integration`; source commit `fef382599333d78228e5f322ee6987ee289d090b`.
- All three seed-round jobs and the aggregate audit job completed successfully.
- Combined artifact: `cbpfr-c5g7-six-layout-high-budget-confirmation-2026-10-12` (artifact ID `11747677926`, SHA-256 `be48b17c2c336a97d08673d191457b9c695853759180116f5382f636b4c93019`).
- Analysis report: [CBPFR_C5G7_SIX_LAYOUT_HIGH_BUDGET_ANALYSIS_2026-10-12.md](../reports/CBPFR_C5G7_SIX_LAYOUT_HIGH_BUDGET_ANALYSIS_2026-10-12.md).

## Automated outputs

The combined artifact contains:
- three complete study directories with raw statepoints and case manifests;
- `run_level_results.csv`, exported after statepoint/MGXS hashes, manifests, settings, source identity, group boundaries, and tallies were audited;
- `export_audit.json`, recording evidence provenance and integrity;
- `objective_audit.json`, with descriptive per-layout estimates and Student-t intervals for repeated-run metrics;
- `budget_comparison.json`, comparing higher-budget estimates against the archived smoke runs.

The exported CSV SHA-256 is `3eb5d575cc5076ead39de04907beddd25fa2310465b508208579bbd4a5c0192d`. Raw outputs are retained as GitHub Actions artifacts for 90 days; preserve a separate long-term archive before expiration.

## Results and interpretation

The integrity audit found all six layouts in each round, 18 runs, unique seeds and statepoint hashes, one common MGXS hash, common settings, and corrected group-structure audits. The evidence integrity result is PASS.

Descriptive mean relative fission-rate-peaking proxy ranks are MMUU (1), MUMU (2), MUUM (3), UUMM (4), UMUM (5), and UMMU (6), with lower proxy values ranked first. MMUU and MUMU are close and should not be presented as meaningfully different without a stronger comparison. The proxy is not absolute power or a safety metric.

The completed budget comparison is descriptive only. The smoke and high-budget runs use different seeds/budgets and do not establish convergence. The result does not certify benchmark validity, physical superiority, absolute power, reactor safety, or quantum advantage.

## Fail-closed decision policy

The workflow does not infer or tune a candidate-specific acceptable (k_{eff}) band from the observed data and does not select a physical winner. The objective audit status is `EVIDENCE_INTEGRITY_PASS_DESIGN_SELECTION_BLOCKED`.

A downstream selector QUBO may be evaluated only after the physical acceptance criteria and tally mapping are justified and predeclared. The integrated pipeline's numerical parameters must be treated as caller-declared criteria, not inferred from the six observed outputs. Do not run it with arbitrary limits merely to force a winner.

## Remaining release blockers

1. Independent review/sign-off against the primary C5G7 specification and generated geometry/material/boundary inputs.
2. Independent review of mesh-to-assembly mapping and the exact definition/normalization of the fission-rate peaking proxy against an appropriate reference tally.
3. Review of source/eigenvalue stationarity diagnostics; absence of a statistically detectable linear trend is not proof of convergence.
4. Predeclare and justify a model-appropriate decision rule, including any (k_{eff}) acceptance criterion, before selecting a winner.
5. Compare CB-PFR fairly with QUBO-only and simple baseline selectors on the same evidence and criteria. Preserve negative and inconclusive results.
6. Archive raw statepoints, manifests, hashes, environment, code/version, configuration, and analysis outputs for long-term reproduction.

## Release status

```text
COMPUTE_EXECUTION                  PASS
RUN_EVIDENCE_INTEGRITY             PASS
SIX_LAYOUT_DESCRIPTIVE_SCREEN      COMPLETE
STATISTICAL_CONVERGENCE_CERTIFIED  NO
PHYSICAL_VALIDATION_CERTIFIED      NO
CB-PFR SUPERIORITY ESTABLISHED     NO
WINNER SELECTED                    NO
```

This is a completed computational screening package suitable for independent review, not a certified physical validation or reactor-safety assessment.
