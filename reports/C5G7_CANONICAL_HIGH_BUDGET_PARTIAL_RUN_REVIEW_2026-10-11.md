# Canonical high-budget C5G7 run — partial artifact review (2026-10-11)

## Executive disposition

**Run status: CANCELLED after two complete transport cases; one case incomplete.**  
**Scientific status: partial high-budget numerical evidence preserved; convergence review and physical validation remain open.**

Workflow: https://github.com/thenextw4ng/cb-pfr/actions/runs/38103032861  
Workflow run ID: `38103032861`  
Branch: `research/c5g7-corrected-canonical-run-20261011`  
Commit: `2771ae3dc157936440d602f895d760b043ca7bdb`  
Artifact: `c5g7-canonical-high-budget-screen-7000-10000` (artifact ID `11691113062`)  
Artifact ZIP SHA-256: `76bccd4c28916d27655c2c53c821645709a520397325714abbdba6cca0efa45e`

The artifact was uploaded despite cancellation because the upload step was configured with `if: always()`. It contains completed results for seeds 720000 and 730000 and partial setup files for seed 740000. The aggregate-gate step was skipped, so there is no aggregate PASS from this workflow.

## Exact run configuration

- OpenMC 0.16.0, multi-group eigenvalue mode, one thread.
- 7,000 total batches; 100 inactive; 6,900 active.
- 10,000 particles per batch.
- Candidate: `c5g7-2x2-UMMU`, recorded positions `p00=UO2, p01=MOX, p10=MOX, p11=UO2`.
- MGXS SHA-256 in both completed cases: `a4328a7b012321fbe8f661745aa135f0a2eecd34cf475429e160865204acb129`.
- Each completed case has a `statepoint.7000.h5`, settings, transport log, source-convergence diagnostics, assembly-fission analysis, and a raw-HDF5 audit.

## Completed cases

| Seed | (k_{eff}) mean | OpenMC reported standard deviation | Raw HDF5 audit | Source/convergence diagnostic |
|---:|---:|---:|---|---|
| 720000 | 1.1864684089 | 0.0000939356 | PASS, 22 checks, 0 failures | DIAGNOSTIC_REVIEW_REQUIRED |
| 730000 | 1.1864698949 | 0.0000946303 | PASS, 22 checks, 0 failures | DIAGNOSTIC_REVIEW_REQUIRED |
| 740000 | No completed statepoint in artifact | — | Not produced | Not produced |

The two completed estimates differ by (1.4860\times10^{-6}), approximately 0.149 pcm in (k_{eff}). This difference is much smaller than either run's reported within-run Monte Carlo standard deviation. With only two completed seeds, this is a descriptive consistency observation, not a reliable between-seed uncertainty estimate or proof of convergence.

The assembly-integrated fission-rate peaking proxy was 1.8686199 (seed 720000) and 1.8691310 (seed 730000), a relative difference of about 0.0273%. The code explicitly defines this as max assembly-integrated fission rate divided by the mean across the four fuel assemblies. Its uncertainty is not propagated for correlated mesh bins. Therefore this comparison is descriptive only: it is not absolute power, a safety metric, or a defensible basis for selecting a best layout.

## Blocking diagnostic: entropy-box warnings

Both completed transport logs contain exactly 7,000 occurrences of:

`WARNING: Fission source site(s) outside of entropy box.`

The generated settings use a 51×51×1 entropy mesh with z bounds ([-1,1]) cm. The generated 2-D geometry has no finite z boundary, so the fission source can extend axially beyond this finite entropy mesh. This is a likely explanation for the warning and must be verified against OpenMC's entropy-mesh semantics. The warning means the entropy trace cannot currently be treated as a clean source-convergence acceptance test. It does **not**, by itself, establish that the (k_{eff}) estimate is wrong; it does block claiming that the entropy diagnostic passed.

The descriptive (k)-generation half-window difference was approximately -17.42 pcm for seed 720000 and -21.22 pcm for seed 730000. The analysis script correctly leaves both as `DIAGNOSTIC_REVIEW_REQUIRED`; no predeclared acceptance threshold is supplied, and a scalar window comparison alone cannot certify convergence.

## Follow-up code hardening after artifact review

The generated settings revealed that the current adapter had narrowed the entropy mesh z bounds to `[-1, 1]` even though the 2-D C5G7 geometry has no finite axial boundary. The adapter has now been changed on `main` to use one z bin spanning `[-1e50, 1e50]`, matching the upstream model's intended unbounded-axial treatment:

- Adapter fix commit: `6acce23615d4f5186343281d1f9b5e7a6db27979`
- Test assertions for the axial extent: `a60c3d5e33bab9786d533c971b650f1ea008cd66`
- The intermediate-budget workflow was changed to require manual dispatch so a code edit does not automatically start 18 transport runs: `ef5837ba3648c946ac6214316b6d8c1741dba045`

These are code-level corrections, **not proof that the entropy-mesh fix works in transport**. CI was still queued/in progress at the time of this report, and no post-fix OpenMC run has validated the absence of warnings. Run a small targeted diagnostic only after CI passes; do not restart the high-budget run just to test the fix.

## What is verified versus not verified

### Verified by retained artifacts
- Two independent seed values completed the configured 7,000-batch transport run.
- Both completed cases have distinct statepoint hashes and matching seed/settings manifests.
- Both raw-HDF5 audits passed 22 checks with zero failures.
- Both use the same non-empty MGXS hash and the same run profile.
- I independently inspected the archived MGXS HDF5 attributes; both files contain the exact group edges `[1e-5, 0.0635, 10, 100, 1000, 500000, 1000000, 20000000]` eV and share the same SHA-256.
- The generated 3×3 core lattice maps the UMMU fuel positions to UO₂/MOX/MOX/UO₂ and retains the five reflector cells in the right column and bottom row.
- Both generated a four-assembly fission-rate proxy and descriptive convergence traces.

### Not established
- The third seed completed; its statepoint and audit are absent.
- The aggregate numerical gates passed; the aggregation step was skipped.
- Source/entropy convergence passed; the logs contain entropy-box warnings and the diagnostic status remains review-required.
- A design-specific (k_{eff}) acceptance band or predeclared physical objective is approved.
- The modified four-position layout is validated as the full canonical C5G7 benchmark.
- Physical superiority, reactor safety, absolute power, or CB-PFR effectiveness on a reactor model is demonstrated.
- The legacy `fresh / once_burned / twice_burned` QUBO is mapped to C5G7 UO2/MOX materials; those states remain unmapped.

## Recommended close-out actions without another high-budget run

1. Preserve this artifact and the two completed statepoints; do not rerun the same 210-million-particle configuration merely to replace the missing third seed before diagnosing the entropy warning.
2. Correct or explicitly disable the entropy diagnostic for this 2-D model, or define a physically justified finite axial domain/mesh. Add a test that asserts no entropy-box warnings for a run intended to use source-entropy diagnostics.
3. Re-run lightweight static audits against the archived inputs: group-edge array, MGXS provenance, material IDs/compositions, geometry-to-position mapping, settings/seed hashes, and the exact C5G7 reference scope.
4. If time/resources allow after the diagnostic is corrected, run a smaller targeted check first; only then decide whether a new high-budget seed is necessary. Do not imply that a small check replaces the cancelled high-budget profile.
5. Report the two completed cases as **partial high-budget numerical evidence**, not as a completed three-seed study or physical validation.
6. Keep independent reactor-physics review and an approved, predeclared acceptance protocol as explicit open gates.

## Reproducibility

Download the artifact from the workflow page above. The ZIP digest listed at the top is the integrity identifier for the preserved archive. Each case's `CASE_RESULT.json` includes hashes for generated inputs and outputs; the two completed raw-HDF5 audits are under `seed_720000/analysis/raw_hdf5_audit.json` and `seed_730000/analysis/raw_hdf5_audit.json`.

This report records the cancelled run as it actually occurred. It does not manufacture the missing third run, convert a skipped aggregate step into a pass, or claim physical validation.
