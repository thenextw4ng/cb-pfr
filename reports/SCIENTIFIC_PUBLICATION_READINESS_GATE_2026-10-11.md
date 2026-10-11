# Scientific-project and publication-readiness gates — 2026-10-11

## Purpose and decision rule

This record separates software completion, reproducible computational evidence, scientific interpretation, and publication readiness. A green CI run or an OpenMC statepoint audit is not, by itself, physical validation. This file is a gate register, not a claim that all gates have passed.

## Five project gates

| Gate | Required evidence | Current status | Release decision |
|---|---|---|---|
| 1. Candidate design space | Exactly six unique 2×2 UO₂/MOX placements, two assemblies of each fuel type, with reflector positions p02, p12, p20, p21, p22 fixed; generated lattice must match the manifest | Software contract and regression tests are implemented; latest CI workflow run 38104812729 passed on Python 3.10–3.12 | Software/input-contract gate passes for the checked revision; this does not validate reactor physics |
| 2. Run provenance | Each case has actual settings, explicit seed, build and transport logs, statepoint, exact input hashes, shared MGXS identity, and a passing raw-HDF5 audit | End-to-end audit added; the 18-run smoke workflow 38104812849 completed successfully and uploaded the raw study artifact | Smoke-run provenance gate passes for that artifact; do not infer production-budget evidence from smoke settings |
| 3. Reproducible tally analysis | Tally values extracted from statepoints; spatial mapping and integration independently checked; within-run Monte Carlo uncertainty kept separate from between-seed variation | Reanalysis workflow 38103279843 passed; fission-peaking values are preserved as a dimensionless exploratory proxy | Data extraction is reproducible; spatial/objective validation and benchmark-grade convergence remain open |
| 4. Fair candidate comparison | Predeclared objective and design-specific acceptance rule; common adequate budget; repeated independent seeds; uncertainty propagation; justified treatment of candidates outside acceptance limits | Three seed rounds exist only at 100 batches, 10 inactive, 1,000 particles/batch; canonical high-budget workflow 38103032861 was still in progress at the last status check | Not passed. No winner or physically preferred layout may be claimed |
| 5. Scientifically bounded publication | Manuscript and repository agree; data and code are available; claims distinguish synthetic benchmark, software checks, transport runs, benchmark verification, and physical validation | Scope/limitations are documented, but candidate evaluation and QUBO-to-C5G7 material mapping remain unresolved | A methods/software or exploratory computational manuscript may be drafted with explicit limitations; a claim of physical CB-PFR validation is not publication-ready |

## Verified links

- Main repository: https://github.com/thenextw4ng/cb-pfr
- Python 3.10–3.12 CI and committed-evidence checks: https://github.com/thenextw4ng/cb-pfr/actions/runs/38104812729
- Three-round, six-layout corrected-group smoke workflow and artifact: https://github.com/thenextw4ng/cb-pfr/actions/runs/38104812849
- Fission-objective reanalysis: https://github.com/thenextw4ng/cb-pfr/actions/runs/38103279843
- Higher-budget canonical convergence run (status must be rechecked): https://github.com/thenextw4ng/cb-pfr/actions/runs/38103032861
- End-to-end evidence audit: https://github.com/thenextw4ng/cb-pfr/blob/main/reports/C5G7_END_TO_END_EVIDENCE_AUDIT_2026-10-11.md
- Current remaining-work audit: https://github.com/thenextw4ng/cb-pfr/blob/main/reports/REMAINING_WORK_AUDIT_2026-10-11.md
- Corrected-group smoke report: https://github.com/thenextw4ng/cb-pfr/blob/main/reports/c5g7_corrected_group_repeatability_smoke_2026-10-11.md

## Mandatory scientific blockers

1. **Legacy QUBO mapping:** No defensible mapping is currently documented from abstract `fresh / once_burned / twice_burned` states to C5G7 UO₂/MOX assemblies. Do not claim that the current six-layout placement study validates the legacy CB-PFR QUBO. Keep the C5G7 placement QUBO explicitly separate unless a source-backed material/depletion mapping is developed.
2. **Benchmark identity:** Verify model geometry, materials, boundary conditions, nuclear data, upstream revision, and tally definitions against the primary C5G7 specification. A scalar near a reference value is not sufficient.
3. **Canonical convergence:** Wait for the high-budget canonical workflow to complete, inspect its logs and source-entropy / batch-wise diagnostics, and interpret its gate result. A completed run may still fail a scientific gate.
4. **Spatial tally mapping:** Independently establish the mesh-bin to assembly/pin spatial orientation and integration. The current fission-peaking proxy is not absolute power, a safety metric, or an accepted optimization objective.
5. **Candidate comparison:** Define the k-effective acceptance band and objective protocol before examining or selecting a winner; justify those values from a primary source and model scope. Run the six candidates under a common higher budget with properly paired, independent seeds and statepoints. Propagate uncertainty to the objective and mark unresolved comparisons inconclusive.
6. **Publication package:** Freeze a version; provide a complete reproduction command, environment and data provenance, artifact checksums, run-level CSV, analysis outputs, figures, methods, limitations, and references. Clearly label synthetic versus transport evidence and include negative or inconclusive findings.

## Safe current claim

“CB-PFR is an open research prototype with a reproducible synthetic benchmark, an audited archived C5G7/OpenMC baseline statepoint, and an 18-run exploratory C5G7 UO₂/MOX assembly-placement smoke study. Automated software and artifact-integrity checks are available. Benchmark-grade candidate comparison, spatial-objective validation, and a defensible mapping from the legacy burnup-state QUBO to C5G7 materials remain unresolved.”

## Claims not supported at this stage

Do not claim a physically validated CB-PFR reactor optimizer, validated reactor design, official benchmark acceptance for the six variants, a proven physical winner, reactor-safety improvement, quantum advantage, or independent external replication.

## Completion sign-off checklist

- [ ] Six-layout and reflector contract verified on the exact release commit.
- [ ] Each claimed run has raw statepoint, logs, settings, seed, input hashes, MGXS hash, and a passing evidence audit.
- [ ] High-budget canonical verification and convergence diagnostics reviewed; pass/fail/inconclusive status documented.
- [ ] Spatial mesh orientation and tally aggregation independently checked.
- [ ] Objective and acceptance thresholds predeclared and justified.
- [ ] Six candidates evaluated with a common adequate budget and genuinely independent, paired seed/statepoint records.
- [ ] Uncertainty analysis and sensitivity/robustness analysis complete.
- [ ] Manuscript, figures, tables, source, data, and release metadata are mutually consistent.
- [ ] An independent researcher can reproduce the reported analysis from the archived artifacts.

A checked software gate is not a substitute for any unchecked scientific gate. Publication readiness should be stated at the appropriate scope: software/methods prototype, exploratory computational study, or physically validated application.
