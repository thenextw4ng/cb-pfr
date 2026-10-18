# CB-PFR A–G execution status — 2026-10-18

## Decision at this checkpoint

**Overall physical-validation status: NOT ESTABLISHED.** This is an execution and evidence-tracking report, not a declaration that any gate has passed. The controlling protocol is `reports/CBPFR_SCIENTIFIC_PHYSICAL_VALIDATION_CONTRACT_A-G_2026-10-12.md`; its acceptance criteria must not be loosened after results are seen.

## Current executable work

1. **P4/P5 OpenMC held-out campaign and P6 comparison** — [workflow run #39098770358](https://github.com/thenextw4ng/cb-pfr/actions/runs/39098770358). At the latest inspection, the run had a mixture of completed successful P4 jobs and P5 jobs in progress/queued; the complete six-layout × three-seed phases and aggregate report were not yet available. This cannot yet be treated as a final ranking result.
2. **Canonical C5G7 independent S_N cross-check** — [workflow run #39100496297](https://github.com/thenextw4ng/cb-pfr/actions/runs/39100496297). The pinned independent solver job completed, while comparison against the P4/P5 held-out artifacts was still running. Its current canonical (k_\mathrm{eff}=1.184733) differs from the cited (1.186550) reference by about −181.7 pcm; investigate model/geometry/material/data/settings equivalence before calling it a pass.
3. **Independent S_N transport for all six layouts** — [workflow run #39104899024](https://github.com/thenextw4ng/cb-pfr/actions/runs/39104899024). Three layout jobs were in progress and three queued at the latest inspection. Results are not yet a six-layout comparison.
4. **Deterministic A–G foundation audit** — [workflow run #39105876779](https://github.com/thenextw4ng/cb-pfr/actions/runs/39105876779) completed successfully. It passed the selected exact QUBO, six-layout, objective-protocol, and fail-closed mapping tests. The machine-readable result is available as [artifact #12128143370](https://github.com/thenextw4ng/cb-pfr/actions/runs/39105876779/artifacts/12128143370). This is a software/design-space sub-gate only; its emitted overall status remains `NOT_ESTABLISHED` for physical validation.

The run state is time-dependent; consult the linked Actions pages for the latest status. GitHub Actions status is not a physical-acceptance decision.

## A–G gate matrix

| Gate | Status now | Required closure evidence |
|---|---|---|
| **A — Model identity and benchmark fidelity** | **BLOCKED** | Independently reconcile generated geometry, materials, nuclear data/group structure, settings, boundary conditions and source/eigenvalue procedure against the primary C5G7 specification; record reviewer sign-off or preserve the limitation. |
| **B — Geometry, tally semantics and spatial mapping** | **BLOCKED** | Independently verify mesh bounds/orientation/index order, tally score/filters, region aggregation and correspondence to the reference quantity. A normalized fission-rate proxy is not absolute power. |
| **C — QUBO/design-space correctness** | **SOFTWARE SUB-GATE TESTED; PHYSICAL DECISION BLOCKED** | Exhaustive four-bit enumeration should yield six two-MOX/two-UO₂ layouts; all six have equal cardinality-penalty energy. The physical objective, design constraints and any feasibility bands still need a justified frozen protocol. |
| **D — Integrity, replication and convergence** | **IN PROGRESS / REVIEW REQUIRED** | Finish P4/P5 and six-layout S_N artifacts; re-audit seed-to-statepoint/input correspondence, hashes, run settings, source/eigenvalue stationarity, entropy diagnostics if applicable, and within-/between-seed uncertainty. Do not treat `DIAGNOSTIC_REVIEW_REQUIRED` as a convergence certificate. |
| **E — Physical benchmark validation** | **NOT ESTABLISHED** | Resolve the canonical cross-code discrepancy; compare like-for-like spatial quantities with uncertainty and a predeclared justified criterion; add suitable experimental benchmark evidence if claiming experimental validation. Historical BEAVRS spatial agreement was poor and is not a passing validation result. |
| **F — Fail-closed evidence pipeline** | **SOFTWARE SUB-GATE PASSED; PHYSICAL GATES STILL FAIL-CLOSED** | Run deterministic algorithm tests and ensure missing fidelity/convergence/reference evidence yields BLOCKED/INCONCLUSIVE rather than PHYSICAL_VALIDATION_PASS. A green CI run is necessary but not sufficient. |
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
