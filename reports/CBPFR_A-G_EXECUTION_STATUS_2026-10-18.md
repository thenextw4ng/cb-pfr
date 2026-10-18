# CB-PFR A–G execution status — 2026-10-18

## Decision at this checkpoint

**Overall physical-validation status: NOT ESTABLISHED.** This is an execution and evidence-tracking report, not a declaration that any gate has passed. The controlling protocol is `reports/CBPFR_SCIENTIFIC_PHYSICAL_VALIDATION_CONTRACT_A-G_2026-10-12.md`; its acceptance criteria must not be loosened after results are seen.

## Current executable work

1. **P4/P5 OpenMC held-out campaign and P6 comparison** — [workflow run #39098770358](https://github.com/thenextw4ng/cb-pfr/actions/runs/39098770358). At the latest check it had 10 completed, 6 in progress and 14 queued out of 36 P4/P5 matrix jobs. The held-out phase and final P6 decision are not yet complete; do not treat a partial artifact inventory as a final six-layout comparison.
2. **Independent deterministic S_N transports for all six layouts** — [run #39104899024](https://github.com/thenextw4ng/cb-pfr/actions/runs/39104899024) completed all six layout jobs and its aggregator successfully. Its first aggregate summary was superseded because the CSV had stale field names and the mask incorrectly counted four instrument-tube cells as fuel.
3. **Corrected six-layout S_N artifact audit** — [posthoc workflow #39110583084](https://github.com/thenextw4ng/cb-pfr/actions/runs/39110583084) completed successfully, artifact [#12130630849](https://github.com/thenextw4ng/cb-pfr/actions/runs/39110583084/artifacts/12130630849). JSON/CSV are consistent for all six layouts; source hash matches metadata; source-derived layout signature matches metadata; five fixed reflector positions pass; expected solver settings are checked. The corrected count is **1,056 true fuel pins + 4 central instrument-tube cells + 96 zero-power guide-tube cells** per four-assembly block. This remains a deterministic computational screen, not physical validation.
4. **A–G software/design-space audit** — [run #39110583165](https://github.com/thenextw4ng/cb-pfr/actions/runs/39110583165) completed successfully.
5. **Full repository regression and fail-closed closeout** — [run #39110583360](https://github.com/thenextw4ng/cb-pfr/actions/runs/39110583360) completed successfully on Python 3.12: **211 unit tests passed**, examples/compilation passed, retained datasets were re-audited, and the workflow asserted physical validation remains `NOT_ESTABLISHED`. Artifact [#12130267528](https://github.com/thenextw4ng/cb-pfr/actions/runs/39110583360/artifacts/12130267528) preserves the reports.
6. **Canonical-only cross-code comparison / P4-P5 posthoc audit** — [workflow #39110217157](https://github.com/thenextw4ng/cb-pfr/actions/runs/39110217157) is still waiting for the P4/P5 OpenMC campaign to finish. Earlier unmasked spatial-error outputs are superseded. Once P5 records are complete, the cross-code workflow should use the corrected 1,056-true-fuel-pin mask and re-audit raw HDF5 before publishing any six-layout comparison.

The detailed run audit is recorded in [`reports/C5G7_SIX_LAYOUT_SN_RUN_AUDIT_2026-10-18.md`](C5G7_SIX_LAYOUT_SN_RUN_AUDIT_2026-10-18.md). The source/model-fidelity audit is [`reports/C5G7_SOURCE_MODEL_FIDELITY_AUDIT_2026-10-18.md`](C5G7_SOURCE_MODEL_FIDELITY_AUDIT_2026-10-18.md), and the independent-review packet is [`reports/CBPFR_INDEPENDENT_REVIEW_PACKET_A-G_2026-10-18.md`](CBPFR_INDEPENDENT_REVIEW_PACKET_A-G_2026-10-18.md). Run state is time-dependent; a green workflow is not a physical-acceptance decision.

## A–G gate matrix

| Gate | Status now | Required closure evidence |
|---|---|---|
| **A — Model identity and benchmark fidelity** | **PARTIALLY AUDITED; INDEPENDENT REVIEW OPEN** | The pinned source, lattice, boundary conditions, tally definition and deliberate energy-group patch are documented in the model-fidelity audit. The pinned S_N solver's own mesh study documents the remaining −181.7 pcm offset at 16 cells per pin as its Cartesian/digital-disk discretization bias; do not misclassify it as a clean validation pass or unexpected proof of model-input error. Independently reconcile actual generated OpenMC files against the primary C5G7 specification and record reviewer sign-off or preserve unresolved limitations. |
| **B — Geometry, tally semantics and spatial mapping** | **CORRECTION IMPLEMENTED; INDEPENDENT REVIEW OPEN** | The comparison is being corrected to use the same 1,056 true fuel-pin positions in both codes, excluding four central instrument/fission-chamber positions and 96 guide-tube bins. The first mask erroneously counted all 1,060 positive Sₙ bins as fuel. The newer tests check local pin coordinates, fuel-only renormalization, duplicate coordinates, and asymmetric HDF5 x/y-bin order. Independently verify mesh bounds/orientation/index order, tally filters/scores, physical-region aggregation, and correspondence to the cited reference quantity. A normalized fission-rate proxy is not absolute power. |
| **C — QUBO/design-space correctness** | **SOFTWARE SUB-GATE TESTED; PHYSICAL DECISION BLOCKED** | Exhaustive four-bit enumeration should yield six two-MOX/two-UO₂ layouts; all six have equal cardinality-penalty energy. The physical objective, design constraints and any feasibility bands still need a justified frozen protocol. |
| **D — Integrity, replication and convergence** | **IN PROGRESS / REVIEW REQUIRED** | Finish P4/P5 and six-layout S_N artifacts; re-audit seed-to-statepoint/input correspondence, hashes, run settings, source/eigenvalue stationarity, entropy diagnostics if applicable, and within-/between-seed uncertainty. Do not treat `DIAGNOSTIC_REVIEW_REQUIRED` as a convergence certificate. |
| **E — Physical benchmark validation** | **NOT ESTABLISHED** | Characterize the independent S_N solver's documented mesh-resolution bias and finish like-for-like spatial comparisons with uncertainty and a justified criterion; independently review generated OpenMC inputs and add suitable experimental benchmark evidence if claiming experimental validation. Historical BEAVRS spatial agreement was poor and is not a passing validation result. |
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
