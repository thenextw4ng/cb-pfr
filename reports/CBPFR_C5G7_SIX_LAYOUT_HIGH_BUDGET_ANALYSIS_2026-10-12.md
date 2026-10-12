# CB-PFR C5G7 Six-Layout High-Budget Analysis
Date: 2026-10-12

## Executive decision

**Run execution and evidence integrity: PASS. Physical validation: NOT CERTIFIED. CB-PFR superiority: NOT ESTABLISHED. Design winner: NONE.**

GitHub Actions run: https://github.com/thenextw4ng/cb-pfr/actions/runs/38229045726  
Source commit: `fef382599333d78228e5f322ee6987ee289d090b`  
Combined artifact: `cbpfr-c5g7-six-layout-high-budget-confirmation-2026-10-12`  
Artifact ID: `11747677926`  
Artifact SHA-256: `be48b17c2c336a97d08673d191457b9c695853759180116f5382f636b4c93019`

## What completed

- Three independent seed rounds: 820000, 830000, 840000.
- Six layouts per round; 18 completed OpenMC runs total.
- Each run used 7,000 total batches, 500 inactive batches, 10,000 particles per batch, and 2 threads.
- Nominal histories: 1.26 billion across 18 runs; active histories after inactive batches: 1.17 billion.
- All six layouts are present in each round; seeds and statepoint hashes are unique.
- All 18 records report the same MGXS hash, corrected seven-group boundaries, and common compute settings.
- Export integrity audit status: `RUN_EVIDENCE_EXPORTED_INTEGRITY_PASS_PHYSICAL_VALIDATION_NOT_CERTIFIED`.
- Objective audit status: `EVIDENCE_INTEGRITY_PASS_DESIGN_SELECTION_BLOCKED`.

## Aggregate results

The table below reports means across three independent runs per layout. The fission-peaking quantity is a **relative fission-rate proxy**, not validated absolute power or a safety limit. (k_{eff}) is the simulated eigenvalue for this model and configuration; it is not a design acceptance verdict without a predeclared, model-appropriate criterion.

| Layout | Mean (k_{eff}) | Between-seed SD of (k_{eff}) | Mean reported within-run SD | Mean relative fission-peaking proxy | Between-seed SD of proxy | Descriptive proxy rank (lower is better) |
|---|---:|---:|---:|---:|---:|---:|
| MMUU | 1.1436721 | 0.0000507 | 0.0000953 | 1.295369 | 0.000667 | 1 |
| MUMU | 1.1437002 | 0.0000971 | 0.0000956 | 1.296364 | 0.001056 | 2 |
| MUUM | 1.1562627 | 0.0000859 | 0.0000953 | 1.316149 | 0.001297 | 3 |
| UUMM | 1.2046416 | 0.0001034 | 0.0000970 | 1.816091 | 0.000894 | 4 |
| UMUM | 1.2046883 | 0.0000588 | 0.0000972 | 1.816720 | 0.000191 | 5 |
| UMMU | 1.1864986 | 0.0001402 | 0.0000970 | 1.867100 | 0.001541 | 6 |

The descriptive ranking is strictly for the reported fission-rate peaking proxy and is not a global CB-PFR ranking. In particular, the two lowest-proxy layouts MMUU and MUMU are very close: their mean proxy difference is approximately 0.000995 (about 0.077% of the MMUU mean), and only three independent runs per layout are available. Do not over-interpret this small ordering.

## Budget comparison

The workflow's archived smoke-budget comparison reports nontrivial shifts between smoke and high-budget means for several layouts. The comparison explicitly uses different seeds and budgets, so it is descriptive and is not a convergence certificate. The completed high-budget results improve the repeatability of the six-layout screen, but do not alone prove source convergence or benchmark validity.

## What the data supports

1. **Execution completeness:** the six-layout × three-seed compute campaign completed successfully.
2. **Evidence integrity:** 18 run records, unique statepoints/seeds, common MGXS provenance, settings, and group-structure checks passed.
3. **Descriptive differentiation:** the simulated layouts show different (k_{eff}) and relative fission-rate-peaking values. The low-proxy group is MMUU/MUMU/MUUM; UMMU has the highest proxy among these six.
4. **Repeatability at this compute profile:** between-seed scatter is small for these reported scalar outputs relative to the smoke campaign, but three seeds are a limited sample and do not establish a general reliability guarantee.

## What the data does NOT support

- No formal physical-validation pass or official C5G7 benchmark acceptance.
- No validated absolute power, flux, thermal-hydraulic limit, or reactor-safety conclusion.
- No final physical winner: no approved design-specific (k_{eff}) acceptance band or independently reviewed tally-to-reference comparison is recorded.
- No proof that CB-PFR outperforms QUBO-only selection or a simple physical-score baseline. This artifact contains the six-layout OpenMC results and audits, not a paired, predeclared CB-PFR-versus-baseline decision evaluation.
- No quantum advantage claim.
- No direct mapping of legacy burnup-state QUBO variables to UO₂/MOX physics.

## Required closeout actions

1. Obtain independent review/sign-off against the primary C5G7 specification and the generated geometry/material/boundary inputs.
2. Review the mesh-to-assembly mapping and exact definition/normalization of the fission-rate peaking proxy against an appropriate reference tally. Do not call it absolute power.
3. Document source/eigenvalue stationarity diagnostics and have the limitations reviewed; absence of a significant linear trend is not proof of convergence.
4. Predeclare the scientific decision rule and acceptable (k_{eff}) criterion appropriate to the stated research question before choosing a winner. Do not select an acceptance band after looking at the candidate results.
5. Run a fair, paired evaluation of CB-PFR against QUBO-only and simple baseline selectors using the same candidate set, evidence, and decision criteria. Preserve negative or inconclusive outcomes.
6. Once these checks are complete, freeze the result package and publish the raw-data manifest, checksums, code/version, environment, run configuration, analysis outputs, and limitations.

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

This is a computational benchmark screening package suitable for independent review, not a certified physical validation or reactor-safety assessment.
