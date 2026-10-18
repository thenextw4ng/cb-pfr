# CB-PFR A–G execution status — 2026-10-18

## Decision at this checkpoint

**Overall physical-validation status: NOT ESTABLISHED.** This is an execution and evidence-tracking report, not a declaration that any gate has passed. The controlling protocol is `reports/CBPFR_SCIENTIFIC_PHYSICAL_VALIDATION_CONTRACT_A-G_2026-10-12.md`; its acceptance criteria must not be loosened after results are seen.

## Current executable work

1. **P4/P5 OpenMC held-out campaign and P6 comparison** — [workflow run #39098770358](https://github.com/thenextw4ng/cb-pfr/actions/runs/39098770358). Latest direct API check: the 36 P4/P5 matrix jobs include 10 completed, 6 in progress and 20 queued. The P6 aggregate is not yet available. The full six-layout × three-seed record set and report cannot yet be treated as final.
2. **Canonical C5G7 independent S_N cross-check** — [workflow run #39100496297](https://github.com/thenextw4ng/cb-pfr/actions/runs/39100496297). The pinned independent solver completed, but its original in-workflow postprocessing is still running against an older analysis snapshot. Its initial canonical (k_\mathrm{eff}=1.184733) differs from the cited (1.186550) reference by about −181.7 pcm. The older unmasked spatial-analysis output is **superseded**; use the corrected posthoc workflows below instead.
3. **Independent S_N transport for all six layouts** — [workflow run #39104899024](https://github.com/thenextw4ng/cb-pfr/actions/runs/39104899024). Latest direct API check: three of six layout transports completed and three remained in progress. Preliminary console values are solver outputs only; no noncanonical layout is being checked against the canonical reference as an acceptance band.
4. **A–G foundation audit including corrected spatial-mask regression tests** — [workflow run #39106781314](https://github.com/thenextw4ng/cb-pfr/actions/runs/39106781314) completed successfully. The cross-code scripts compiled and imported, the fuel-only mask regression tests passed, and the QUBO/design-space/objective/mapping tests passed. This closes selected software sub-gates, not physical validation.
5. **Extended retained-evidence audit** — [workflow run #39105968459](https://github.com/thenextw4ng/cb-pfr/actions/runs/39105968459) completed successfully; [artifact #12128790628](https://github.com/thenextw4ng/cb-pfr/actions/runs/39105968459/artifacts/12128790628) preserves the reports. The prior 18-run low-budget dataset passed integrity checks but **failed the canonical scalar screening gate**. The corrected-group 18-run dataset passed record integrity across six layouts but selected no winner, because physical acceptance and spatial mapping remain blocked.
6. **Corrected posthoc cross-code comparison, including all six layouts** — [workflow run #39106731078](https://github.com/thenextw4ng/cb-pfr/actions/runs/39106731078) is waiting for the P4/P5 campaign and six-layout S_N workflow to finish, then will re-audit raw HDF5 statepoints, use the corrected 1,060-pin fuel mask (excluding 96 non-fuel bins), and compare all six layouts. Earlier unmasked spatial-error values must not be reused.

The source-level fidelity review is recorded in [`reports/C5G7_SOURCE_MODEL_FIDELITY_AUDIT_2026-10-18.md`](C5G7_SOURCE_MODEL_FIDELITY_AUDIT_2026-10-18.md). The run state is time-dependent; consult linked Actions pages for latest status. Green workflow status is not a physical-acceptance decision.

## A–G gate matrix

| Gate | Status now | Required closure evidence |
|---|---|---|
| **A — Model identity and benchmark fidelity** | **PARTIALLY AUDITED; INDEPENDENT REVIEW OPEN** | The pinned source, lattice, boundary conditions, tally definition and deliberate energy-group patch are documented in the model-fidelity audit. Independently reconcile actual generated input files against the primary C5G7 specification and record reviewer sign-off or preserve unresolved limitations. |
| **B — Fuel-mask correction implemented; independent mapping review open** | The comparison now excludes 96 non-fuel bins and computes relative errors on the same 1,060 fuel-pin mask. Independently verify mesh bounds/orientation/index order, tally filters/score, physical-region aggregation, and correspondence to the cited reference quantity. A normalized fission-rate proxy is not absolute power. |
| **C — QUBO/design-space correctness** | **SOFTWARE SUB-GATE TESTED; PHYSICAL DECISION BLOCKED** | Exhaustive four-bit enumeration should yield six two-MOX/two-UO₂ layouts; all six have equal cardinality-penalty energy. The physical objective, design constraints and any feasibility bands still need a justified frozen protocol. |
| **D — Integrity, replication and convergence** | **IN PROGRESS / REVIEW REQUIRED** | Finish P4/P5 and six-layout S_N artifacts; re-audit seed-to-statepoint/input correspondence, hashes, run settings, source/eigenvalue stationarity, entropy diagnostics if applicable, and within-/between-seed uncertainty. Do not treat `DIAGNOSTIC_REVIEW_REQUIRED` as a convergence certificate. |
| **E — Physical benchmark validation** | **NOT ESTABLISHED** | Resolve the canonical cross-code discrepancy; compare like-for-like spatial quantities with uncertainty and a predeclared justified criterion; add suitable experimental benchmark evidence if claiming experimental validation. Historical BEAVRS spatial agreement was poor and is not a passing validation result. |
| **F — Fail-closed evidence pipeline** | **SELECTED SOFTWARE SUB-GATES PASSED; PHYSICAL GATES STILL FAIL-CLOSED** | Run deterministic algorithm tests and ensure missing fidelity/convergence/reference evidence yields BLOCKED/INCONCLUSIVE rather than PHYSICAL_VALIDATION_PASS. A green CI run is necessary but not sufficient. |
| **G — Synthesis and release claim audit** | **BLOCKED ON A–F** | Keep manuscript, workstation, manifests and artifact hashes aligned. Claims must not exceed the evidence in the passed gates. |

## Interpretive guardrails

- The four-bit QUBO is a cardinality constraint, not a neutron-physics objective: it cannot discriminate among the six feasible layouts.
- The published canonical C5G7 reference is applicable to its specified canonical case, not an automatic (k_\mathrm{eff}) pass/fail band for all five material permutations.
- A deterministic cross-code comparison supports code-to-code analysis, not experimental validation by itself.
- Three independent seeds per layout are a pilot design; 10,000 bootstrap resamples from those seeds are not 10,000 independent transport experiments.
- No run count by itself establishes universal physical validity or reactor design/safety qualification.

## Allowed claim at this checkpoint

“CB-PFR is an uncertainty-aware screening and ranking workflow under evaluation on a specified six-layout C5G7 model using a declared relative fission-rate-shape proxy.”

Do **not** claim universal physical superiority, reactor safety, experimental validation, or validated reactor-design-method status from the current evidence.
