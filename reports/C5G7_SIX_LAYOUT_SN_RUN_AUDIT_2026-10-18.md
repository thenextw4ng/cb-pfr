# Audit of Completed Six-Layout Independent C5G7 S_N Run — 2026-10-18

## Executive disposition

**Run execution: PASS. Corrected artifact/model-identity screen: PASS. Physical validation: NOT ESTABLISHED.**

The original run [#39104899024](https://github.com/thenextw4ng/cb-pfr/actions/runs/39104899024) completed all six independent deterministic S_N layout jobs and the aggregate job successfully. The original aggregate contained two reporting defects: it treated four instrument-tube cells with tiny positive fission as true fuel pins, and its CSV used stale column names. The raw solver outputs were preserved; no transport was repeated. The corrected posthoc job [#39110583084](https://github.com/thenextw4ng/cb-pfr/actions/runs/39110583084) re-read the six original artifacts and created a matching JSON/CSV report. Its artifact is [#12130630849](https://github.com/thenextw4ng/cb-pfr/actions/runs/39110583084/artifacts/12130630849).

The corrected report status is `COMPLETE_COMPUTATIONAL_SCREEN`, with six expected layouts and no record-level artifact problems. That status applies to the computational screen and file/mapping checks only; it is not benchmark acceptance, experimental validation, a reactor-safety finding, or proof that a layout is physically superior.

## 1. Execution, settings and provenance

- Workflow: [C5G7 six-layout independent S_N transport screen #39104899024](https://github.com/thenextw4ng/cb-pfr/actions/runs/39104899024).
- Source code: [EmreSakarya/c5g7-2d-transport-benchmark](https://github.com/EmreSakarya/c5g7-2d-transport-benchmark), pinned commit `db421c969ee2de83e2d2ae2b14bda368567b558d`.
- Shared settings recorded in the six artifact manifests: 16 cells per pin, 24 azimuthal directions, 4 polar directions, 3 inner passes, 4 OpenMP threads; compile flags `-O3 -march=native -fopenmp -ffree-line-length-none`.
- All six layout-specific artifacts contain a metadata JSON, solver log, pin-power CSV, patched Fortran source, and flux/map outputs.
- Corrected posthoc validation confirms for each layout that (i) the actual patched Fortran source SHA-256 matches the metadata hash, (ii) material layout reconstructed from the source matches the metadata signature, (iii) the five reflector positions remain assigned to reflector material, and (iv) solver settings match the expected profile.
- The solver source defines `tol=1e-5` and `maxout=800`. The last printed source iteration in the logs is between 390 and 430, well below the cap. The program prints detailed convergence residuals every ten iterations, so its exact terminal residual/iteration is not present in the retained log. Therefore the source's internal stop-rule inference is recorded, but no stronger claim of independently certified convergence is made.
- Full regression and fail-closed audit on the same revision passed: [#39110583360](https://github.com/thenextw4ng/cb-pfr/actions/runs/39110583360), with **211 unit tests passing**. The dedicated A–G software audit also passed: [#39110583165](https://github.com/thenextw4ng/cb-pfr/actions/runs/39110583165).

## 2. Pin mask correction

The block consists of a 34×34 set of mesh positions, i.e. 1,156 total positions across the four 17×17 assemblies. The solver CSV has:
- **1,056 true fuel pins** (264 per assembly),
- **4 central instrument/fission-chamber positions** (one in each assembly) with very small but positive fission because the simplified chamber material includes trace fissile content,
- **96 guide-tube positions** with zero fission.

An earlier script equated “positive fission” with “fuel pin”, incorrectly including the four instrument cells and reporting their tiny values as the minimum fuel-pin power. The corrected mask excludes both the four central instrument positions and the 96 zero-power guide positions. Both codes' maps are now normalized over the same 1,056 actual fuel pins for true-fuel pin shape comparisons. The raw solver CSV/log bytes are unchanged; their SHA-256 values are retained in the corrected summary. The corrected script also checks local pin row/column values, rejects duplicate coordinates, validates the exact 1,156-bin block, and confirms JSON/CSV fields and counts match.

## 3. Corrected six-layout results

The metrics below are from the independent deterministic S_N solver, normalized over the 1,056 true fuel pins per layout. They are descriptive numerical outputs, not a ranking validated against OpenMC or experiments.

| Layout signature | (k_\mathrm{eff}) | Maximum normalized true-fuel pin power | Minimum normalized true-fuel pin power |
|---|---:|---:|---:|
| MMUU | 1.141478 | 1.722286 | 0.301434 |
| MUMU | 1.141478 | 1.722286 | 0.301434 |
| MUUM | 1.154058 | 1.697060 | 0.218818 |
| UMMU | 1.184733 | 2.344035 | 0.217344 |
| UMUM | 1.203136 | 2.239888 | 0.161440 |
| UUMM | 1.203136 | 2.239888 | 0.161440 |

The corrected report's descriptive low-to-high order for maximum normalized true-fuel pin power is **MUUM, MMUU/MUMU, UMUM/UUMM, UMMU**. This is a simple sort of one deterministic code's output; it is not a CB-PFR decision and does not include OpenMC between-seed uncertainty.

The source/log/CSV hashes are present in the machine-readable [corrected summary artifact #12130630849](https://github.com/thenextw4ng/cb-pfr/actions/runs/39110583084/artifacts/12130630849). For all six records, the patched-source hash matched metadata, the source-derived layout signature matched the artifact label, the fixed-reflector check passed, and the record status was `PASS_RUN_ARTIFACTS`.

## 4. Canonical UMMU comparison and interpretation

Only UMMU is the canonical arrangement for the cited 2-D C5G7 reference. At the specified 16-cells-per-pin discretization, the independent solver reports (k_\mathrm{eff}=1.184733), or about **−181.7 pcm** relative to the cited 1.186550 reference. The pinned solver's own [README and mesh-convergence study](https://github.com/EmreSakarya/c5g7-2d-transport-benchmark/blob/db421c969ee2de83e2d2ae2b14bda368567b558d/README.md) document the remaining bias at this grid resolution as related to the Cartesian/digital-disk treatment of curved pin boundaries. Thus it is a known discretization limitation, not a zero-bias oracle. With the corrected true-fuel normalization, UMMU's max/min are 2.344035 and 0.217344; the published MCNP values (2.498 and 0.232) are not met exactly at this S_N mesh resolution.

Do **not** apply the canonical UMMU (k_\mathrm{eff}) or MCNP pin-power values as a pass/fail band for the other five permutations. Those layouts represent different material arrangements, while the benchmark reference applies to the specified canonical case. No layout has been classified as physically feasible, safe, best, or validated from this screen.

## 5. Remaining blockers

1. **OpenMC comparison:** the held-out P4/P5 OpenMC campaign [#39098770358](https://github.com/thenextw4ng/cb-pfr/actions/runs/39098770358) was still incomplete at the last status check. The six-layout OpenMC-to-S_N comparison cannot be finalized until its 18 P5 statepoints (three seeds/layout) and raw-HDF5 audits are complete.
2. **Spatial quantity equivalence:** OpenMC mesh-bin fission-rate tally and the deterministic solver's normalized pin-power output are related but not identical response quantities. Keep the comparison as a relative shape diagnostic.
3. **Independent reviewer:** source provenance, model modifications, fuel/instrument mask, tally mapping and adequacy of S_N discretization still require qualified independent review.
4. **Decision rule:** no justified physical acceptance band is defined for the five noncanonical permutations. A lower normalized peak-pin result from this deterministic solver alone is not evidence of a physically superior or safer reactor design.
5. **Convergence reporting:** retained logs do not include terminal outer-iteration residuals; a future rerun could be instrumented to preserve final residuals explicitly if that diagnostic is needed, but this does not invalidate the completed computational screen's file-level result.

## Conclusion

The correct audit conclusion is that the requested GitHub run **completed all six deterministic layout transports and passed a corrected, hash-aware computational artifact audit**. The updated analysis now distinguishes true fuel pins from instrument-tube and guide-tube positions and exports consistent JSON/CSV. It produces useful, reproducible numerical differences between the six material arrangements under this solver. It does **not** establish physical validation, OpenMC cross-code agreement, a CB-PFR winner, reactor safety, or universal physical superiority.

## Provenance

- Transport run: [#39104899024](https://github.com/thenextw4ng/cb-pfr/actions/runs/39104899024)
- Corrected summary: [#39110583084](https://github.com/thenextw4ng/cb-pfr/actions/runs/39110583084), artifact #12130630849
- A–G software audit: [#39110583165](https://github.com/thenextw4ng/cb-pfr/actions/runs/39110583165)
- Full repository regression: [#39110583360](https://github.com/thenextw4ng/cb-pfr/actions/runs/39110583360), 211 tests passing
- Pinned S_N source: `db421c969ee2de83e2d2ae2b14bda368567b558d`
