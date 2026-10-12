# CB-PFR A–G Evidence Closeout — 2026-10-12

**Purpose:** record what was verified from the canonical high-budget C5G7 artifact and distinguish software/provenance evidence from physical validation.

**Overall status:** `SOFTWARE_CHECKS_GREEN; CANONICAL_NUMERICAL_SCREEN_PASS; FULL_PHYSICAL_VALIDATION_BLOCKED`.

This report does not assert that all seven gates have passed. It closes the evidence review to the extent supported by artifacts currently available and identifies the remaining non-negotiable blockers. The project scope remains frozen to A–G.

## Evidence source and provenance

- GitHub Actions run: [38196703024](https://github.com/thenextw4ng/cb-pfr/actions/runs/38196703024)
- Artifact: `c5g7-canonical-high-budget-screen-7000-10000`, ID `11725784076`
- Artifact SHA-256 reported by GitHub: `b996708634ff41491b0323bdac11d5ab2574c6716d42fca1a8bf449795aca953`
- Workflow source commit: `e086af2860797cc935c1db1d1d9305f256183537`
- Pinned upstream source: `https://github.com/mit-crpg/benchmarks.git`, commit `ba41bee54320ada0b4ac39a0dd2ca3c1d090a450`
- OpenMC: `0.16.0`, verified from the saved statepoint HDF5 metadata and the workflow's pinned environment.
- Settings per run: 7,000 total batches; 500 inactive; 10,000 particles/batch; 1 thread; three seeds `720000`, `730000`, `740000`.
- Each saved raw-HDF5 audit passed **22/22 checks**. The original workflow completed all three transport runs and their raw audits, but aggregation failed because source-convergence JSON/CSV files had not been generated before the aggregator was called.

## A — Model identity and provenance

**Status: `INPUT_PROVENANCE_VERIFIED; INDEPENDENT_SPECIFICATION_REVIEW_PENDING`.**

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

**Remaining blocker:** these checks prove file identity and internal provenance, not full fidelity to the primary OECD/NEA specification. Independent sign-off on material definitions, geometry, boundary conditions, and benchmark correspondence is not recorded.

## B — Mesh-to-assembly mapping

**Status: `STATIC_MAPPING_AND_SPATIAL_SHAPE_SANITY_CHECK_PASS; PHYSICS_VALIDATION_BLOCKED`.**

The saved model uses a 51×51×1 mesh spanning `[-32.13, 32.13]` cm in x/y. This gives 1.26 cm bins; each 17×17 fuel assembly spans 21.42 cm. The generated geometry shows the expected 3×3 lattice with a 2×2 fuel block and fixed reflector row/column. The tally includes `flux`, `fission`, and `nu-fission`. The reducer's four 17×17 blocks are consistent with the pinned source's top-down RectLattice row ordering and the declared x/y mesh bounds.

The reported assembly quantity is an integrated `fission` tally and the peaking factor is dimensionless. It is a **relative fission-rate proxy**, not absolute power in watts.

A published 2-D C5G7 study reports reference assembly powers of 492.8 for the inner UO₂ assembly, 211.7 for each MOX assembly, and 139.8 for the outer UO₂ assembly (Frontiers in Energy Research, Table 1: https://www.frontiersin.org/journals/energy-research/articles/10.3389/fenrg.2020.00124/full). After normalizing both the three-run mean integrated fission-rate tally and those published assembly-power values to unit total, the maximum relative difference between the four position fractions is 0.179%. This is a useful independent **spatial-shape sanity check** and is consistent with the declared position ordering.

**Remaining blocker:** the OpenMC quantity is an integrated `fission` event-rate tally, whereas the published reference is assembly power. They are related but not identical physical quantities, and the saved statepoint does not contain a heating/power tally. Therefore this comparison does not satisfy a strict same-quantity benchmark validation; no power-validation claim is permitted. Static source review and synthetic indexing tests also do not replace independent model sign-off.

## C — QUBO and design-space correctness

**Status: `SOFTWARE_FORMULATION_AND_ENUMERATION_TESTS_PASS; PHYSICAL_SELECTION_BLOCKED`.**

- The design enumerator yields six unique arrangements of four fuel positions, each with exactly two UO₂ and two MOX; the five reflector positions remain fixed.
- The canonical `UMMU` arrangement is identified as the reference arrangement.
- The C5G7 design QUBO encodes `A(sum(y)-2)^2`. Tests exhaustively compare direct penalty energy with the expanded upper-triangular QUBO for all 16 binary vectors and check invalid vectors/cardinality.
- The separate one-hot layout-selection QUBO has tests for energy consistency, infeasible candidates, invalid bands, and fail-closed behavior.

This is a C5G7 assembly-placement reformulation, **not** a reproduction or material mapping of the legacy fresh/once-burned/twice-burned QUBO.

**Remaining blocker:** no physical winner may be selected. A design-specific acceptable (k_{eff}) band has not been approved, and only the canonical layout has the present high-budget confirmation set. The objective remains a screening proxy.

## D — Data integrity and reproducibility

**Status: `THREE-RUN CANONICAL ARTIFACT INTEGRITY PASS; WORKFLOW REPAIR NOT YET END-TO-END VERIFIED`.**

- Three distinct seeds and three distinct statepoint hashes are present.
- Raw HDF5 audits pass 22/22 checks per run.
- Geometry and MGXS hashes are common across runs; computational settings are the same apart from the intentionally distinct seed and run-specific file paths.
- Statepoint, summary, raw audit, assembly-fission output, settings, MGXS, and logs are preserved in the source artifact.

The original workflow failed only at aggregation because it did not generate the source-convergence files required by its own aggregator. A repair was committed on PR #50 to generate the JSON/CSV diagnostics before aggregation. The subsequent repository test matrix is green, but the repaired canonical workflow/recovery workflow has not yet been executed end-to-end on GitHub Actions.

## E — Metrics and benchmark protocol

**Status: `PROVISIONAL_SCALAR_SCREEN_PASS; FULL_BENCHMARK_ACCEPTANCE_BLOCKED`.**

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

Saved source/eigenvalue diagnostics were reconstructed from the original HDF5 traces without rerunning transport. The second-half-minus-first-half (k)-generation differences were +45.61, +38.09, and −21.48 pcm for seeds 720000, 730000, and 740000. First-to-last-quarter entropy differences were −0.0000685, −0.0019471, and −0.0010348. These are descriptive diagnostics only; the protocol has no justified predeclared trace threshold and the traces still require review. No automatic source-convergence certificate is claimed.

## F — CI and fail-closed integration

**Status: `UNIT/CONTRACT TEST MATRIX PASS; REPAIRED CANONICAL WORKFLOW NOT YET RUN END-TO-END`.**

- Current PR #49 head `439f916a9306c8fe2832ac3e3338bddbb44f5814`: all six reported Python 3.10/3.11/3.12 test-matrix check runs passed.
- Current PR #50 head `040ed70db5f87ac7640049f21c5b77f7d8b4f11d`: all six reported Python 3.10/3.11/3.12 test-matrix check runs passed.
- PR #50 adds source-convergence JSON/CSV generation before aggregation, installs and activates pinned OpenMC 0.16.0 in the recovery workflow, and aligns the inactive-batch fallback at 500.
- Regression tests assert that diagnostics precede aggregation, artifact upload runs even after a failure, and the recovery environment includes OpenMC.

The green test matrix is software evidence only. The repaired high-budget/recovery workflow has not yet been executed end-to-end on GitHub Actions. The recovery workflow is introduced on PR #50 and needs to be present on the repository's default branch before a normal manual dispatch can be used. PR #50 remains draft/open and has not been merged.

## G — Analysis, reporting, and release

**Status: `EVIDENCE REPORT RECORDED; FINAL PHYSICAL-VALIDATION RELEASE BLOCKED`.**

The canonical scalar result, per-run uncertainty, between-seed variability, hashes, raw audit results, and descriptive source diagnostics are now recorded. A final research release must preserve the distinction between (1) software-tested, (2) numerically screened, and (3) physically validated.

### Remaining release blockers

1. Obtain an independent primary-specification/model-identity review (A).
2. Complete a benchmark-compatible spatial tally comparison using the actual saved statepoint and reviewed mesh mapping (B).
3. Review the full source-convergence traces and record an evidence-based interpretation; do not invent a threshold after seeing results (D/E).
4. Execute the repaired canonical workflow or recovery workflow end-to-end on GitHub Actions and archive its output (D/F).
5. Keep physical layout selection blocked until the design-specific (k_{eff}) acceptance band and tally mapping/objective are approved (C/E).

No additional algorithm, metric, experiment, or cosmetic redesign is authorized by this closeout. Repeat transport only if an actual technical failure or evidence gap makes the saved results uninterpretable; do not rerun to obtain a preferred result.

## References

- OECD/NEA, *Benchmark on Deterministic Transport Calculations Without Spatial Homogenisation: A 2-D/3-D MOX Fuel Assembly Benchmark*, NEA/NSC/DOC(2003)16: https://www.oecd-nea.org/jcms/pl_13548/benchmark-on-deterministic-transport-calculations-without-spatial-homogenisation
- Published C5G7 assembly/pin-power reference comparison (Frontiers in Energy Research, 2020): https://www.frontiersin.org/journals/energy-research/articles/10.3389/fenrg.2020.00124/full
- Pinned model source: https://github.com/mit-crpg/benchmarks/tree/ba41bee54320ada0b4ac39a0dd2ca3c1d090a450
- Current workflow repair PR: https://github.com/thenextw4ng/cb-pfr/pull/50
- Scientific readiness tests/report PR: https://github.com/thenextw4ng/cb-pfr/pull/49
