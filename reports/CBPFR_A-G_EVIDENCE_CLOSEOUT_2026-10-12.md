# CB-PFR A–G Evidence Closeout — 2026-10-12

**Governing acceptance contract:** [Scientific and Physical Validation Contract A–G](https://github.com/thenextw4ng/cb-pfr/blob/main/reports/CBPFR_SCIENTIFIC_PHYSICAL_VALIDATION_CONTRACT_A-G_2026-10-12.md). The gates target physical/scientific validation; passing software tests or numerical screens alone does not close them.

**Purpose:** record what was verified from the canonical high-budget C5G7 artifact and distinguish software/provenance evidence from physical validation.

**Overall status:** `SOFTWARE_TESTS_AND_RECOVERY_PASS; CANONICAL_NUMERICAL_SCREEN_PASS; SPATIAL_SHAPE_SANITY_CHECK_PASS; SOURCE_CONVERGENCE_AND_FULL_PHYSICAL_VALIDATION_REVIEW_OPEN`.

This report does not assert that all seven gates have passed. It closes the evidence review to the extent supported by artifacts currently available and identifies the remaining non-negotiable blockers. The project scope remains frozen to A–G.

## Evidence source and provenance

- Original transport run: [38196703024](https://github.com/thenextw4ng/cb-pfr/actions/runs/38196703024)
- Original transport artifact: `c5g7-canonical-high-budget-screen-7000-10000`, ID `11725784076`
- Recovered analysis run: [38207010156](https://github.com/thenextw4ng/cb-pfr/actions/runs/38207010156), completed successfully on 2026-10-12
- Recovered artifact: `c5g7-canonical-recovered-analysis-38196703024`, ID `11727463825`, SHA-256 `6384b82f9981a2fd3ec271e88f10478be84880526be0ae72c7199da02a679c7e`
- The recovery re-used the saved statepoints; it did not rerun transport.
- Workflow source commit: `e086af2860797cc935c1db1d1d9305f256183537`
- Pinned upstream source: `https://github.com/mit-crpg/benchmarks.git`, commit `ba41bee54320ada0b4ac39a0dd2ca3c1d090a450`
- OpenMC: `0.16.0`, verified from the saved statepoint HDF5 metadata and the workflow's pinned environment.
- Settings per run: 7,000 total batches; 500 inactive; 10,000 particles/batch; 1 thread; three seeds `720000`, `730000`, `740000`.
- Each saved raw-HDF5 audit passed **22/22 checks**. The original workflow completed all three transport runs and their raw audits, but aggregation failed because source-convergence JSON/CSV files had not been generated before the aggregator was called.

## A — Model identity and provenance

**Status: `INPUT_PROVENANCE_VERIFIED; PINNED-UPSTREAM SOURCE MATCH REVIEWED; INDEPENDENT BENCHMARK SIGN-OFF PENDING`.**

For each seed, all **30 recorded output files** were re-hashed and compared with that run's `output_hashes_after_run` manifest: **30/30 matched per run**, with zero missing files and zero mismatched hashes (90 file-hash checks total). This includes geometry XML, materials XML, settings XML, MGXS HDF5, generated builders, statepoints, summaries, tally outputs, logs, and copied model source files.

| Input / output | SHA-256 by seed |
|---|---|
| Geometry XML (all three runs) | `f71a6c422b2f1d4d8342334824007a20f1471141f5330d0d1ca0b51e9dfe5f33` |
| MGXS HDF5 (all three runs) | `a4328a7b012321fbe8f661745aa135f0a2eecd34cf475429e160865204acb129` |
| Materials XML, seed 720000 | `3a9342bfd3e8a062655f0ddaee557b09c24ad5d9b7f7981cd88d7279ab60f977` |
| Materials XML, seed 730000 | `fc199ae2eee51c682a1d072dd835938a390c18be87f96d2e86b5f5315f8d63b1` |
| Materials XML, seed 740000 | `25419b18ee668c27141efd339544a2a2c060f7e828ed6b3bf27cc9e3d4659bd7` |
| Settings XML, seed 720000 | `c01f0e0145be700e02c5ddd18bd87d6e39cdccc6733b0e42429208b9f9e1c02d` |
| Settings XML, seed 730000 | `ca046730f27ba2092f0ed6da346bef739020e07f993deb2cc4a5aaa1f292e815` |
| Settings XML, seed 740000 | `6a4024ff298964b98ff2a50d31fee905f602020d041a307614e749d6dc10bd9b` |
| Statepoint, seed 720000 | `db098b04a16cdc4771fb469c82a65be214327adc79742d04bb25f1b6589e29e1` |
| Statepoint, seed 730000 | `c060252df030789e1a7072fe8f71c7849a2e8f2920540a72436352c030b7a562` |
| Statepoint, seed 740000 | `a36a386c0a108a138f767750c103598d0b96ee82ed6eaab50cfa914cdf03e179` |

The settings hashes differ as expected because each run has a distinct seed. The materials XML hashes differ because each XML contains the absolute path to its run-specific MGXS file; the MGXS content hash itself is identical. The generated builder is also seed-specific. All three runs report the standard C5G7 seven-group boundaries: `[1e-5, 0.0635, 10, 100, 1000, 500000, 1000000, 20000000]` eV.

Compared against the pinned upstream source at commit `ba41bee54320ada0b4ac39a0dd2ca3c1d090a450`, the production 2-D builder preserves the upstream 3×3 lattice layout, assembly pitch and extent, mixed reflective/vacuum boundary definitions, 7-group C5G7 data definitions, source-box definition, and mesh/tally definitions. Production changes visible in the builder are runtime settings (7000 batches, 500 inactive, seed) and the added convergence/evidence plumbing. The upstream reference itself uses a log-spaced group structure in `materials.py`; the production artifact's MGXS is separately audited to the standard C5G7 boundaries. This difference is explicitly recorded and the historical production scalar using the nonstandard structure is not used as a comparison target.

**Remaining blocker:** the source-code/input comparison is a strong provenance check, not independent sign-off by a benchmark specialist. Record this as `UPSTREAM_SOURCE_MATCH_REVIEWED; INDEPENDENT_BENCHMARK_SIGNOFF_PENDING`, not as full physical validation.

## B — Mesh-to-assembly mapping

**Status: `MESH_MAPPING_REVIEWED; NORMALIZED_ASSEMBLY_POWER_DISTRIBUTION_AGREES_WITH_REFERENCE_UNCERTAINTY`.**

The saved model uses a 51×51×1 mesh spanning `[-32.13, 32.13]` cm in x/y. This gives 1.26 cm bins; each 17×17 fuel assembly spans 21.42 cm. The generated geometry shows the expected 3×3 lattice with a 2×2 fuel block and fixed reflector row/column. The tally includes `flux`, `fission`, and `nu-fission`. The reducer's four 17×17 blocks are consistent with the pinned source's top-down RectLattice row ordering and the declared x/y mesh bounds.

The reported assembly quantity is an integrated `fission` tally and the peaking factor is dimensionless. It is a **relative fission-rate proxy**, not absolute power in watts.

A published 2-D C5G7 study reports reference assembly powers of 492.8 for the inner UO₂ assembly, 211.7 for each MOX assembly, and 139.8 for the outer UO₂ assembly (Frontiers in Energy Research, Table 1: https://www.frontiersin.org/journals/energy-research/articles/10.3389/fenrg.2020.00124/full). A separate C5G7 transport study explicitly defines normalized pin power from the fission reaction rate, (R_f = sum_g Sigma_f,g * phi_g * V), which supports comparison of normalized integrated fission-rate tallies with normalized assembly-power fractions (https://www.nst.sinap.ac.cn/article/id/5293). After normalizing both the three-run mean integrated fission-rate tally and the published assembly-power values to unit total, the maximum relative difference across the four assembly fractions is 0.179%. This is a reproducible **exploratory normalized-shape screen**, not a closed physical-validation gate: the tally is a fission-rate proxy rather than a direct power tally, and the earlier comparison did not propagate the published reference uncertainties through normalization or combine them with between-run uncertainty. The separate evidence review reports exploratory combined-uncertainty diagnostics and documents their assumptions; independent review of tally/reference comparability remains required. This does not establish absolute power in watts or validate other tallies such as flux.

**Reproducible spatial audit artifact:** the comparison is now machine-readable in `results/c5g7_canonical_high_budget_2026-10-12/spatial_reference_audit.json` and generated by `scripts/audit_c5g7_spatial_reference.py` from the three saved run-level `assembly_fission.json` records. The canonical scalar aggregator's `spatial_reference_tally_reviewed: false` remains accurate for what that aggregator itself evaluated; the separate spatial audit is included in the repository and wired into the matrix confirmation workflow. Keep those evidence records distinct. This closes reproducibility of the normalized shape comparison, not source convergence or full physical validation.

The comparison depends on the published reference configuration and assembly ordering matching this model; the mapping has been checked against the pinned source geometry and the stated 3×3 lattice orientation. Independent benchmark-specialist sign-off remains desirable.

## C — QUBO and design-space correctness

**Status: `SOFTWARE_FORMULATION_AND_ENUMERATION_TESTS_PASS; PHYSICAL_SELECTION_BLOCKED`.**

- The design enumerator yields six unique arrangements of four fuel positions, each with exactly two UO₂ and two MOX; the five reflector positions remain fixed.
- The canonical `UMMU` arrangement is identified as the reference arrangement.
- The C5G7 design QUBO encodes `A(sum(y)-2)^2`. Tests exhaustively compare direct penalty energy with the expanded upper-triangular QUBO for all 16 binary vectors and check invalid vectors/cardinality.
- The separate one-hot layout-selection QUBO has tests for energy consistency, infeasible candidates, invalid bands, and fail-closed behavior.

This is a C5G7 assembly-placement reformulation, **not** a reproduction or material mapping of the legacy fresh/once-burned/twice-burned QUBO.

**Remaining blocker:** no physical winner may be selected. A design-specific acceptable (k_{eff}) band has not been approved, and only the canonical layout has the present high-budget confirmation set. The objective remains a screening proxy.

## D — Data integrity and reproducibility

**Status: `THREE-RUN ARTIFACT INTEGRITY PASS; RECOVERY WORKFLOW END-TO-END PASS; SOURCE-CONVERGENCE INTERPRETATION OPEN`.**

- Three distinct seeds and three distinct statepoint hashes are present.
- Raw HDF5 audits pass 22/22 checks per run.
- Geometry and MGXS hashes are common across runs; computational settings are the same apart from the intentionally distinct seed and run-specific file paths.
- Statepoint, summary, raw audit, assembly-fission output, settings, MGXS, and logs are preserved in the source artifact.

The original transport workflow failed only at aggregation because it did not generate source-convergence files required by its own aggregator. The repaired recovery workflow has now executed end-to-end successfully: it installed OpenMC 0.16.0, downloaded the original saved artifact, generated per-seed JSON/CSV diagnostics from the saved statepoints, ran the repository aggregator, and uploaded artifact `11727463825`. This is a post-processing recovery, not a new transport run. The remaining D/E issue is scientific interpretation of the saved traces, not missing diagnostic files.

## E — Metrics and benchmark protocol

**Status: `PROVISIONAL_SCALAR_SCREEN_PASS; SPATIAL-SHAPE SANITY CHECK PASS; CONVERGENCE REVIEW AND FULL BENCHMARK ACCEPTANCE BLOCKED`.**

Reference target used by the repository protocol: (k_{eff}=1.18655), reference standard uncertainty (0.000095). The combined uncertainty calculation uses the reference uncertainty and the empirical between-seed standard error in quadrature.

| Seed | (k_{eff}) mean | Reported within-run SD | Fission-rate peaking factor |
|---:|---:|---:|---:|
| 720000 | 1.1863182340 | 9.419 pcm | 1.866680 |
| 730000 | 1.1865450004 | 9.698 pcm | 1.869350 |
| 740000 | 1.1866164010 | 9.617 pcm | 1.866938 |

| Aggregate metric | Result |
|---|---:|
| Mean (k_{eff}) | 1.1864932118 |
| Between-seed sample SD | 15.568 pcm |
| Pooled within-run reported SD | 9.579 pcm |
| Difference from reference | −5.679 pcm |
| Combined-uncertainty z-score | −0.434 |
| Maximum individual-run reported SD | 9.698 pcm |
| Mean fission-rate peaking factor | 1.867656 |
| Between-seed SD of peaking factor | 0.001473 |

The provisional project screens pass: three replicates, unique statepoints, common settings/MGXS/group structure, absolute reference difference ≤100 pcm, absolute combined z ≤2, and maximum reported per-run SD ≤10 pcm. These are internal screens, **not official OECD/NEA acceptance criteria**.

The earlier three-seed production sweep also contains all six layouts under a shared corrected MGXS hash and matched 5,000-batch / 500-inactive / 5,000-particle settings. The table below is a comparative **screening dataset**, not a declaration that any layout is physically optimal. Between-seed SD is computed across the three per-run (k_{eff}) means.

| Layout | Mean (k_{eff}) | Between-seed SD | Mean fission-rate peaking factor |
|---|---:|---:|---:|
| UMMU | 1.186641723 | 0.000221548 | 1.867103 |
| MMUU | 1.143837765 | 0.000251822 | 1.296822 |
| MUMU | 1.143845311 | 0.000084678 | 1.297834 |
| MUUM | 1.156076452 | 0.000182843 | 1.317288 |
| UMUM | 1.204725175 | 0.000349910 | 1.814476 |
| UUMM | 1.204661207 | 0.000411585 | 1.815106 |

Source artifacts: [seed 620000](https://github.com/thenextw4ng/cb-pfr/actions/runs/38182056526), with matching study artifacts for seeds 630000 and 640000 in the same run. These results establish that the six candidates were evaluated consistently at the production-screen settings; they do **not** determine a winner. The objective must state how (k_{eff}), the fission-rate proxy, and any feasibility constraints are treated before one arrangement can be called preferable.

Saved source/eigenvalue diagnostics were generated by the repaired repository workflow from the original statepoints, without rerunning transport. The second-half-minus-first-half `k_generation` differences were +45.61, +38.09, and −21.48 pcm; first-to-last-quarter means changed by +42.06, +65.05, and +23.99 pcm for seeds 720000, 730000, and 740000 respectively. Entropy first-to-last-quarter differences were −0.0000685, −0.0019471, and −0.0010348 on a trace mean near 9.74. The entropy shifts are small in relative terms, but the generation-eigenvalue quarter shifts are not negligible compared with the reported 9.4–9.7 pcm within-run standard deviations. The first 500 (inactive) batches were also inspected directly from the saved trace. Mean Shannon entropy over five consecutive 100-batch windows was:
- seed 720000: 9.74717, 9.73424, 9.74141, 9.74001, 9.73700;
- seed 730000: 9.74998, 9.73438, 9.74114, 9.74401, 9.73850;
- seed 740000: 9.74264, 9.73943, 9.73292, 9.74610, 9.74697.
These inactive-window values fluctuate without a common monotonic trend across seeds, and the active entropy quarter means remain within about 0.003 entropy units per run. This is evidence against an obvious entropy drift, but entropy is only a scalar proxy for the spatial source distribution and cannot by itself prove equilibrium.

The OLS slopes and window differences are descriptive, correlated batch traces—not independent observations or formal convergence tests. **Scientific interpretation: source/eigenvalue stationarity is not yet demonstrated by a predeclared acceptance protocol.** The diagnostic status remains `DIAGNOSTIC_REVIEW_REQUIRED`; no automatic convergence certificate is claimed. This does not invalidate the scalar result by itself, but it blocks a full physical-validation claim until an expert review or an explicitly justified follow-up protocol resolves it.

As an **exploratory, post-hoc diagnostic only**, I fitted a linear trend against active-batch index with Newey–West/HAC standard errors (lag 100). The estimated `k_generation` slopes per 1,000 active batches were +0.0001080 (p=0.257), +0.0000721 (p=0.504), and −0.0000153 (p=0.895) for seeds 720000, 730000, and 740000. The corresponding entropy-slope p-values were 0.591, 0.539, and 0.761. These tests do not detect a statistically significant linear trend at conventional levels, but this is not proof of stationarity: the lag choice was exploratory, batch observations are correlated, and no acceptance threshold was predeclared. The appropriate interpretation remains **no clear linear trend detected, convergence not certified**.

## F — CI and fail-closed integration

**Status: `UNIT/CONTRACT TEST MATRIX PASS; RECOVERY WORKFLOW END-TO-END PASS; PRODUCTION TRANSPORT WORKFLOW STILL NEEDS ITS OWN CONFIRMATION RUN`.**

- Scientific readiness branch commit `55b061d867ebc1cd92e17b429a4cd35068c6bc0a`: all six reported Python 3.10/3.11/3.12 test-matrix check runs passed.
- Workflow repair commit `c0c7cefdf26e91806c7481f2d2645d2a63a4183f`: all six reported Python 3.10/3.11/3.12 test-matrix check runs passed.
- Recovery workflow run [38207010156](https://github.com/thenextw4ng/cb-pfr/actions/runs/38207010156): job completed successfully; all six analysis/recovery steps passed.
- Repository test run [38207010089](https://github.com/thenextw4ng/cb-pfr/actions/runs/38207010089): completed successfully.
- PR #50 adds source-convergence JSON/CSV generation before aggregation, installs and activates pinned OpenMC 0.16.0 in the recovery workflow, and aligns the inactive-batch fallback at 500.
- Regression tests assert that diagnostics precede aggregation, artifact upload runs even after a failure, and the recovery environment includes OpenMC.

The green test matrix and successful recovery workflow establish software/workflow readiness for post-processing the saved run. The canonical high-budget transport workflow itself has not been rerun after the workflow fix, because the existing three transport results were already complete and recovery succeeded without repeating expensive transport. PR #50 was merged into `main` on 2026-10-12; the recovered artifact is archived under run [38207010156](https://github.com/thenextw4ng/cb-pfr/actions/runs/38207010156). The remaining work is scientific review of the traces and physical acceptance evidence, not recovery of missing diagnostic files.

## G — Analysis, reporting, and release

**Status: `EVIDENCE REPORT RECORDED; FINAL PHYSICAL-VALIDATION RELEASE BLOCKED`.**

The canonical scalar result, per-run uncertainty, between-seed variability, hashes, raw audit results, and descriptive source diagnostics are now recorded. A final research release must preserve the distinction between (1) software-tested, (2) numerically screened, and (3) physically validated.

### Remaining release blockers

1. Obtain independent sign-off on fidelity to the primary C5G7 specification. The pinned upstream source match is reviewed, but code provenance is not independent benchmark certification (A).
2. The normalized assembly-power/fission-rate distribution comparison now passes against published reference uncertainty (maximum relative difference 0.179%). Do not extend this result to absolute watts, flux, pinwise power, or full reactor validation without corresponding evidence (B).
3. Complete a documented source/eigenvalue trace review. The available traces are noisy; first-to-last-quarter `k_generation` shifts are +42.06, +65.05, and +23.99 pcm, while entropy shifts are small. The diagnostic script correctly leaves all runs at `DIAGNOSTIC_REVIEW_REQUIRED`. Do not invent a pass threshold after seeing the data. If expert review concludes stationarity is inadequate, predeclare a justified follow-up protocol before any additional transport (D/E).
4. The six-layout, three-seed screening comparison is now documented. Before naming a physical winner, approve a design-specific objective/acceptance band and state how (k_{eff}) and the fission-rate proxy enter the decision; the canonical confirmation run is higher-budget evidence for UMMU only, not confirmation of every candidate (C/E).
5. PR #50 has been merged and the recovery workflow is archived. Review the generated convergence traces and aggregate; run the canonical transport workflow again only if a documented evidence gap remains (D/F/G).

No additional algorithm, metric, experiment, or cosmetic redesign is authorized by this closeout. Repeat transport only if an actual technical failure or evidence gap makes the saved results uninterpretable; do not rerun to obtain a preferred result.

## References

- OECD/NEA, *Benchmark on Deterministic Transport Calculations Without Spatial Homogenisation: A 2-D/3-D MOX Fuel Assembly Benchmark*, NEA/NSC/DOC(2003)16: https://www.oecd-nea.org/jcms/pl_13548/benchmark-on-deterministic-transport-calculations-without-spatial-homogenisation
- Published C5G7 assembly/pin-power reference comparison (Frontiers in Energy Research, 2020): https://www.frontiersin.org/journals/energy-research/articles/10.3389/fenrg.2020.00124/full
- Pinned model source: https://github.com/mit-crpg/benchmarks/tree/ba41bee54320ada0b4ac39a0dd2ca3c1d090a450
- OpenMC's 7-group C5G7 example using the corrected group boundaries: https://github.com/openmc-dev/openmc/blob/develop/examples/pincell_random_ray/build_xml.py
- OpenMC `EnergyGroups` ordering documentation: https://docs.openmc.org/en/stable/_modules/openmc/mgxs/groups.html
- Current workflow repair PR: https://github.com/thenextw4ng/cb-pfr/pull/50
- Final software/A–G integration PR: https://github.com/thenextw4ng/cb-pfr/pull/52
