# CB-PFR A–G Final Evidence Closeout — 2026-10-12

**Overall disposition:** `SOFTWARE_READY; NUMERICAL_SCREEN_PASS; SCIENTIFIC_READY_FOR_INDEPENDENT_REVIEW; NOT_YET_PHYSICALLY_VALIDATED`.

This report records the strongest claim supported by the current evidence. It does not turn a passing CI or a scalar numerical screen into a physical-validation certificate. Scope remains frozen to gates A–G.

## Evidence and reproducibility

- Original canonical high-budget transport run: [38196703024](https://github.com/thenextw4ng/cb-pfr/actions/runs/38196703024)
- Original transport artifact: `c5g7-canonical-high-budget-screen-7000-10000`, ID `11725784076`, SHA-256 `b996708634ff41491b0323bdac11d5ab2574c6716d42fca1a8bf449795aca953`
- Recovery run, using saved statepoints without rerunning transport: [38207010156](https://github.com/thenextw4ng/cb-pfr/actions/runs/38207010156)
- Recovered artifact: [artifact 11727463825](https://github.com/thenextw4ng/cb-pfr/actions/runs/38207010156/artifacts/11727463825), SHA-256 `6384b82f9981a2fd3ec271e88f10478be84880526be0ae72c7199da02a679c7e`
- Workflow repair PR [#50](https://github.com/thenextw4ng/cb-pfr/pull/50) was merged to `main` as commit `00191c838da18a881b0f1f0e7ee4e5ae8e177a3a`.
- Post-merge main CI: [run 38219846637](https://github.com/thenextw4ng/cb-pfr/actions/runs/38219846637), Python 3.10, 3.11 and 3.12 jobs all passed.
- Pinned model source: `https://github.com/mit-crpg/benchmarks.git`, commit `ba41bee54320ada0b4ac39a0dd2ca3c1d090a450`; OpenMC `0.16.0`.
- Canonical settings: 7,000 batches, 500 inactive batches, 10,000 particles/batch, one thread, seeds 720000, 730000, 740000.
- Each of the three raw HDF5 audits passed 22/22 checks. The recovery workflow generated diagnostics using the repository's official scripts, then ran the repository aggregator successfully.

## Gate status summary

| Gate | Current status | Evidence-based disposition |
|---|---|---|
| A — Model identity/provenance | `PROVENANCE_PASS; INDEPENDENT_SPECIFICATION_SIGNOFF_PENDING` | Inputs and run outputs are hash-traceable; pinned-source comparison reviewed. Independent sign-off on fidelity to the primary benchmark specification remains open. |
| B — Geometry/tally mapping | `NORMALIZED_DISTRIBUTION_COMPARISON_PASS` | Mesh/assembly mapping reviewed; normalized fission-rate fractions agree with published assembly-power fractions within the cited reference uncertainties. No absolute-power or flux validation is claimed. |
| C — QUBO/design space/decision | `ENUMERATION_AND_QUBO_TESTS_PASS; FINAL_SELECTION_BLOCKED` | Six arrangements are enumerated; each has two UO₂ and two MOX with five reflectors fixed. The physical objective and acceptable (k_{eff}) band are not approved for final ranking. |
| D — Integrity/reproducibility/convergence | `ARTIFACT_INTEGRITY_AND_RECOVERY_PASS; CONVERGENCE_NOT_CERTIFIED` | Three unique seeds/statepoints, common MGXS and settings, and complete saved diagnostics. Trace interpretation remains exploratory; no predeclared stationarity criterion was available. |
| E — Physical benchmark comparison | `PROVISIONAL_SCALAR_SCREEN_PASS; FULL_VALIDATION_BLOCKED` | Canonical scalar screen and normalized distribution comparison pass their stated provisional checks. Model sign-off, convergence interpretation and approved physical decision protocol remain necessary. |
| F — Fail-closed pipeline/CI | `WORKFLOW_REPAIR_MERGED; MAIN_CI_PASS` | Missing convergence diagnostics are generated before aggregation; recovery workflow passes; post-merge main test matrix is green. These are software/workflow results, not proof of physics validity. |
| G — Final synthesis/release | `EVIDENCE_PACKAGE_RECORDED; PHYSICAL_VALIDATION_RELEASE_BLOCKED` | Claims and limitations are recorded here. The project can be presented as ready for independent validation review, not as physically validated. |

## A — Model identity and provenance

The actual saved model inputs and run outputs were checked against per-run hash manifests. The original artifact contains 30 recorded files per seed; all 30 matched per seed (90 file-hash checks, zero mismatches or missing files). Geometry, settings, MGXS, source/build scripts, statepoints, summaries, tallies and logs are preserved. The MGXS content hash is common across runs, and the actual run MGXS is audited to the standard C5G7 seven-group boundaries:
`[1e-5, 0.0635, 10, 100, 1000, 500000, 1000000, 20000000]` eV.

The pinned upstream source comparison reviewed the 3×3 lattice, 2×2 fuel region, assembly pitch, reflector positions, mixed reflective/vacuum boundary conditions, source box, and mesh/tally setup. The actual generated MGXS uses the standard boundaries, whereas the historical upstream materials script used a different log-spaced structure; the old scalar from that nonstandard structure is explicitly excluded as a benchmark comparison target.

**Remaining A blocker:** this is a traceable source/model review, not independent sign-off by a qualified benchmark reviewer. Keep the gate pending until that review or a documented scope limitation is recorded.

## B — Spatial mapping and reference comparison

The statepoint mesh is 51×51×1 over ([-32.13,32.13]) cm in x/y, yielding 1.26 cm bins; each 17×17 assembly spans 21.42 cm. The four 17×17 fuel blocks map to `p00,p01,p10,p11` in the documented order. The reported score is integrated `fission`, and the peaking factor is `max(assembly fission rate)/mean(assembly fission rate)`; it is a dimensionless relative fission-rate proxy, not power in watts.

A published 2-D C5G7 study reports assembly-power references 492.8 (inner UO₂), 211.7 (each MOX), and 139.8 (outer UO₂), with relative uncertainties 0.10%, 0.18%, and 0.20%, respectively: https://www.frontiersin.org/journals/energy-research/articles/10.3389/fenrg.2020.00124/full

Normalizing the three-run mean integrated fission tallies and the published reference values to unit sum gives relative differences:
- inner UO₂ (`p00`): +0.0530%;
- MOX (`p01`): +0.0344%;
- MOX (`p10`): −0.0395%;
- outer UO₂ (`p11`): −0.1790%.

The maximum absolute relative difference is 0.179%, within the corresponding published relative uncertainties. This supports a **normalized assembly-distribution comparison only**. It does not validate absolute watts, flux, pinwise power, untested configurations, or reactor safety. The machine-generated convergence JSON correctly keeps `spatial_reference_tally_reviewed=false`, because the aggregator itself does not run this separate post-aggregation comparison.

## C — QUBO and decision validity

The design space contains exactly six unique assignments of two UO₂ and two MOX across four fuel positions, with five reflector positions fixed. Exhaustive enumeration and QUBO energy/constraint tests are present in the repository. This is a C5G7 assembly-placement reformulation, not a direct reproduction of Usmanov's fresh/once-burned/twice-burned QUBO.

The six-layout, three-seed screening results are available from run [38182056526](https://github.com/thenextw4ng/cb-pfr/actions/runs/38182056526). They are screening-budget comparisons, not proof of an optimum. The objective template is explicitly not approved for final ranking; a design-specific acceptable (k_{eff}) band and a justified uncertainty-aware physical decision rule must be approved before naming a winner. Only UMMU currently has the 7,000-batch high-budget confirmation set.

## D — Trace and uncertainty diagnosis

Official recovery diagnostics were generated from all 7,000 saved batches per run (500 inactive; 6,500 active). The script intentionally labels each trace `DIAGNOSTIC_REVIEW_REQUIRED` and does not automatically certify convergence.

| Seed | (k_{eff}) first-to-last active-quarter shift | Second-half minus first-half | Entropy first-to-last active-quarter shift |
|---:|---:|---:|---:|
| 720000 | +42.06 pcm | +45.61 pcm | −0.0000685 |
| 730000 | +65.05 pcm | +38.09 pcm | −0.0019471 |
| 740000 | +23.99 pcm | −21.48 pcm | −0.0010348 |

An exploratory OLS trend with Newey–West/HAC standard errors (lag 100) did not detect a statistically significant linear trend in active (k)-generation or entropy traces: (k)-generation slope p-values were 0.257, 0.504 and 0.895; entropy slope p-values were 0.591, 0.539 and 0.761. These are post-hoc diagnostics, not a predeclared acceptance test. Batch traces are correlated; non-significance does not prove stationarity. Entropy is only a scalar proxy for source-distribution stability.

**Remaining D/E blocker:** obtain qualified interpretation of the traces or preregister a scientifically justified follow-up protocol before any new expensive transport. Do not invent thresholds after seeing the results and do not rerun to obtain a preferred result.

## E — Canonical scalar screen

The official repository aggregator returned `NUMERICAL_SCREEN_PASS_FULL_BENCHMARK_STILL_BLOCKED`:

| Metric | Result |
|---|---:|
| Mean (k_{eff}) | 1.1864932118 |
| Between-seed sample SD | 0.000155684 |
| Pooled within-run reported SD | 0.000095788 |
| Difference from reference 1.18655 | −5.679 pcm |
| Combined-uncertainty z-score | −0.434 |
| Maximum individual-run reported SD | 9.698 pcm |

The provisional internal criteria (three replicates, unique statepoints, common settings/MGXS/group structure, absolute reference difference ≤100 pcm, absolute z ≤2, maximum per-run reported SD ≤10 pcm) pass. These are **project screening criteria**, not official OECD/NEA acceptance limits. Scalar agreement does not overcome the open convergence and independent model-review gates.

## F — Workflow repair and verification

PR #50 fixed the missing source-convergence JSON/CSV generation before aggregation, installed and activated pinned OpenMC 0.16.0 in the recovery workflow, aligned the inactive-batch fallback to 500, and added regression tests. The recovery workflow completed end-to-end on the preserved artifact; all three diagnostic outputs were created and the official aggregator completed. PR #50 was merged to main as `00191c838da18a881b0f1f0e7ee4e5ae8e177a3a`. The post-merge main CI matrix passed on Python 3.10, 3.11 and 3.12.

The production transport workflow has not been rerun after this fix because the three transport cases already completed and the recovery workflow succeeded without rerunning transport. This is intentional and avoids unnecessary expensive compute.

## G — Release decision and remaining work

**Current release label:** `SCIENTIFIC_READY_FOR_INDEPENDENT_VALIDATION_REVIEW`, not `PHYSICALLY_VALIDATED`.

Only these actions remain in scope:
1. Record independent primary-specification/model-fidelity review (A).
2. Obtain qualified source/eigenvalue convergence interpretation, or preregister a justified follow-up protocol if the evidence is insufficient (D/E).
3. Approve the physical objective and design-specific (k_{eff}) acceptance rule before final candidate ranking (C/E).
4. Keep all reported claims limited to normalized distribution and scalar quantities actually checked; no absolute-power, flux, pinwise, or safety claims.
5. After those decisions, update the evidence matrix and release package so the paper, UI, analysis and conclusions agree.

No new algorithm, metric, feature, or cosmetic redesign is required. Further transport is allowed only if the documented scientific question and predeclared acceptance protocol make it necessary.

## Primary references

- OECD/NEA C5G7 benchmark specification: https://www.oecd-nea.org/jcms/pl_13548/benchmark-on-deterministic-transport-calculations-without-spatial-homogenisation
- Published C5G7 assembly/pin-power comparison: https://www.frontiersin.org/journals/energy-research/articles/10.3389/fenrg.2020.00124/full
- Pinned upstream source: https://github.com/mit-crpg/benchmarks/tree/ba41bee54320ada0b4ac39a0dd2ca3c1d090a450
- Recovered analysis run: https://github.com/thenextw4ng/cb-pfr/actions/runs/38207010156
- Workflow repair PR: https://github.com/thenextw4ng/cb-pfr/pull/50
