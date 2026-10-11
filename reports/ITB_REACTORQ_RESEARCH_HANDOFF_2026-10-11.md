# ReactorQ Studio — ITB research handoff (2026-10-11)

## Executive status

This package is a reproducible research prototype for a QUBO-constrained UO₂/MOX assembly-layout study using OpenMC's C5G7-derived 2-D model, with a separate CB-PFR selection layer. The software and evidence workflow are substantially implemented. **Physical validation and a defensible physical layout selection are not complete.** This is the conclusion to present to reviewers; it is more credible than turning incomplete evidence into a success claim.

## What is complete and evidenced

### 1. Software and reproducibility
- The four-position layout design space exhaustively enumerates 16 binary assignments; exactly six contain two UO₂ and two MOX.
- The layout adapter validates candidate IDs/material counts, keeps five reflector positions fixed, records seeds/settings/input/output hashes, and preserves raw statepoints.
- Raw-HDF5 audits, mesh-to-assembly spatial checks, repeatability analysis, fission-objective analysis, and a fail-closed selection gate are implemented.
- The CB-PFR test suite passed on Python 3.10, 3.11, and 3.12 in [GitHub Actions run 38110809161](https://github.com/thenextw4ng/cb-pfr/actions/runs/38110809161).
- The synthetic CB-PFR benchmark is a separate body of evidence; it must not be represented as proof of physical reactor effectiveness.

### 2. C5G7 input and spatial structure
- The canonical partial-run artifact's two completed MGXS files were independently inspected. Both share SHA-256 **a4328a7b012321fbe8f661745aa135f0a2eecd34cf475429e160865204acb129** and group edges **[1e-5, 0.0635, 10, 100, 1000, 500000, 1000000, 20000000] eV**.
- The generated UMMU 3×3 lattice records UO₂/MOX/MOX/UO₂ in the four fuel positions and keeps the right reflector column and bottom reflector row fixed.
- The separate 18-case smoke study has an archived structural spatial-mapping audit. This supports the mesh-to-assembly indexing procedure for the generated model; it does not certify the physical model against the full OECD/NEA benchmark specification.

### 3. Preserved high-budget numerical evidence
- Workflow: [C5G7 canonical high-budget screen](https://github.com/thenextw4ng/cb-pfr/actions/runs/38103032861).
- Artifact ID: **11691113062**; ZIP SHA-256: **76bccd4c28916d27655c2c53c821645709a520397325714abbdba6cca0efa45e**.
- Two independent seeds completed 7,000 total batches (100 inactive, 6,900 active; 10,000 particles/batch). Both raw-HDF5 audits passed 22 checks with zero failures.
- (k_{eff}): seed 720000 = 1.1864684089 ± 0.0000939356; seed 730000 = 1.1864698949 ± 0.0000946303.
- The two (k_{eff}) estimates differ by about 0.149 pcm, which is small compared with their within-run statistical uncertainties. This is descriptive agreement between two runs only.
- Seed 740000 did not complete. The aggregate-gate step was skipped. This is not a completed three-seed study.

## Blocking findings and limits

1. Both completed high-budget logs emitted 7,000 warnings each: **Fission source site(s) outside of entropy box.** The generated 2-D geometry is axially unbounded while the adapter had restricted the entropy mesh to z = [-1, 1]. The likely cause was identified; the adapter was corrected to use a wide single z bin, and the regression test passed. A targeted low-budget workflow then completed all 18 cases across six layouts and three seed rounds; all 18 logs had zero entropy-box warnings, the spatial-mapping audit passed all 18 cases, each raw-HDF5 round audit passed 112 checks, and each evidence-integrity audit passed 23 checks ([run 38110780563](https://github.com/thenextw4ng/cb-pfr/actions/runs/38110780563), artifact ID 11690758521, SHA-256 eee7d38c359c7d8d8d92dd8193280890a6f587c826d626bee4db7a9ed75f7551). This validates the fix operationally at smoke budget only. The earlier high-budget runs' entropy diagnostics remain review-required, and the smoke results do not establish benchmark-grade convergence.
2. The source-convergence diagnostics on the two preserved high-budget runs remain **DIAGNOSTIC_REVIEW_REQUIRED**. The entropy trace is not an acceptance-quality source-convergence check for those runs.
3. The fission-peaking proxy is max(assembly-integrated fission rate) / mean(assembly-integrated fission rate). It is not absolute power or a safety metric; uncertainty for correlated mesh bins is not propagated.
4. No approved, predeclared design-specific (k_{eff}) acceptance interval and objective uncertainty budget is available. Do not select a physical winner from the current dataset.
5. Benchmark identity still requires line-by-line review of material compositions, geometry, boundary conditions, MGXS provenance and the applicable OECD/NEA specification. Matching a group-edge array or hash alone is not proof of physical correctness.
6. The legacy CB-PFR categorical states **fresh / once_burned / twice_burned** remain **UNMAPPED** to C5G7 UO₂/MOX. The four-position UO₂/MOX QUBO is a separate formulation.
7. No reactor-safety improvement, quantum advantage, absolute-power result, or physical CB-PFR effectiveness claim is supported.

## Current code/CI changes

- Entropy-mesh axial extent correction: commit **6acce23615d4f5186343281d1f9b5e7a6db27979**.
- Regression test for the corrected mesh bounds: commit **a60c3d5e33bab9786d533c971b650f1ea008cd66**.
- Intermediate-budget 18-run transport workflow made manual-dispatch-only to avoid accidental expensive runs on source edits: commit **ef5837ba3648c946ac6214316b6d8c1741dba045**.
- Python test matrix passed on all three supported Python versions. The low-budget three-seed/six-layout smoke workflow and its archived artifact have been inspected; the corrected mesh produced zero entropy-box warnings. This is smoke-level validation of the fix, not a source-convergence pass for the earlier high-budget cases.

## What to show ITB

Demonstrate the working layout/QUBO preparation and reproducible evidence pipeline. Show the two preserved high-budget statepoints, 22/22 HDF5 audit results, corrected seven-group edges, and the completed smoke-study spatial audit. Then show the explicit blockers and the fail-closed rule: **no physical ranking is issued until the convergence, acceptance-criteria, and independent-review gates pass.**

## Evidence index

- [Partial high-budget run review](C5G7_CANONICAL_HIGH_BUDGET_PARTIAL_RUN_REVIEW_2026-10-11.md)
- [Machine-readable partial run results](../results/c5g7_canonical_partial_2026-10-11.json)
- [End-to-end evidence audit](C5G7_END_TO_END_EVIDENCE_AUDIT_2026-10-11.md)
- [Spatial-mapping audit](C5G7_SPATIAL_MAPPING_AUDIT_2026-10-11.md)
- [Stage 6 scientific evidence matrix](STAGE6_SCIENTIFIC_EVIDENCE_MATRIX_2026-10-11.md)
- [Stage 6 UO₂/MOX integration decision](STAGE6_UOX_MOX_INTEGRATION_DECISION_2026-10-11.md)
- [Stage 6 closure checklist](stage6_closure_checklist.md)
- [Canonical high-budget workflow](https://github.com/thenextw4ng/cb-pfr/actions/runs/38103032861)
- [Corrected-group smoke workflow](https://github.com/thenextw4ng/cb-pfr/actions/runs/38110780563)

## Final disposition

**Software/reproducibility: implemented and automated tests passing.**  
**Exploratory C5G7 transport: completed artifacts exist and are audited.**  
**High-budget canonical screen: partial; two seeds complete, third incomplete, aggregate gate skipped.**  
**Source convergence: open.**  
**Physical benchmark validation and physical CB-PFR effectiveness: not established.**  
**Independent reactor-physics review: still required.**

This is a submission-ready, evidence-limited research handoff, not a certification of reactor physics.
