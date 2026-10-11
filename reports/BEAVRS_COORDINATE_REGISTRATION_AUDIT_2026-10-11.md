# BEAVRS Coordinate Registration Audit — 2026-10-11

## Scope

This is a diagnostic of the completed BEAVRS Cycle-1 day-0 run using the U-235 fission tally. It is not a validation pass and does not modify the original run artifacts.

Run: https://github.com/thenextw4ng/cb-pfr/actions/runs/38119215203  
Pinned model source: https://github.com/mit-crpg/BEAVRS/tree/1ccae04dc3830a5977f08ed7f5f7e1e51ded0d22  
Archived statepoint SHA-256: \`e4b3e565e6b0dd7b67e821d157e1343700717a46559efdadc41c8cf2fa290092\`

## Confirmed facts

- The statepoint contains a 15×15×1 mesh with bounds ±7.5 assembly pitches.
- The comparison uses 58 unique instrumented assembly labels and the corresponding tilt-corrected reference values.
- The current label-to-mesh mapping follows the source template's top-down rows and reverses the row index for increasing physical y, consistent with OpenMC 0.15.3 RectLattice documentation.
- Under the current mapping, the recorded normalized-map Pearson correlation is 0.03236 and RMSE is 0.32892. These are poor spatial agreement.
- The statepoint's mean \(k_\mathrm{eff}\) is 0.9992544 with Monte Carlo standard deviation 0.0007645. Criticality consistency does not establish spatial-map agreement.

## Orientation sensitivity diagnostic

The archived full mesh was re-indexed under the current coordinate mapping and seven alternative rotations/reflections solely to diagnose registration sensitivity. Exploratory correlations were:

| Coordinate transform | Pearson correlation |
|---|---:|
| Current mapping (identity) | 0.0324 |
| Reflect x | 0.2982 |
| Reflect y | -0.1064 |
| Reflect x and y | 0.1964 |
| Transpose x/y | 0.1708 |
| Transpose plus reflect x | 0.3628 |
| Transpose plus reflect y | -0.1064 |
| Transpose plus both reflections | 0.0037 |

These transforms are diagnostic hypotheses, not candidate corrections. The best observed correlation is still modest and was identified after examining the result; adopting it would be post-hoc fitting and is prohibited as validation evidence. This table does **not** establish that the current map is wrong, nor does it establish that any alternative is correct. It establishes that orientation must be resolved independently before another expensive transport run.

## Geometry-plot diagnostic workflow

A plot-only GitHub Actions workflow has been added at `.github/workflows/beavrs-coordinate-audit.yml`. It freezes the same BEAVRS source revision, exports the coordinate crosswalk, renders the upstream OpenMC geometry plots, overlays all 193 assembly labels and marks the 58 instrumented positions in red, and uploads the artifacts **without running neutron transport**. Its purpose is to make coordinate review possible before spending compute on another physics run. The workflow and its resulting plots still require review against the published detector-layout schematic; a successful plot render is not a physical-validation pass.

## Required gate before rerunning transport

1. Create a coordinate crosswalk for all 58 labels showing the detector label, upstream assembly-template row/column, physical assembly center (x,y), and OpenMC mesh bin.
2. Independently compare the crosswalk with the BEAVRS detector-layout schematic and a plot of the generated OpenMC geometry. Do not choose an orientation by comparing correlations.
3. Add a synthetic asymmetric-map test that detects x/y reflection, transpose, and one-bin offsets with known expected results.
4. Confirm that the measurement CSV labels and the generated model use the same named assembly coordinate convention.
5. Only after this gate passes, rerun transport and recompute the predeclared comparison metrics. If spatial agreement remains poor, investigate state matching, detector response, and model-form assumptions rather than tuning the coordinate transform.

## Claim boundary

The run and artifact integrity audit succeeded, but the scientific conclusion remains **physical validation NOT ESTABLISHED**. This audit does not validate CB-PFR's selection benefit, the legacy burnup-state QUBO mapping, or any quantum-hardware advantage.


## Plot-only coordinate audit result — 11 October 2026

The plot-only workflow completed successfully without neutron transport: [run 38120609560](https://github.com/thenextw4ng/cb-pfr/actions/runs/38120609560), [artifact bundle](https://github.com/thenextw4ng/cb-pfr/actions/runs/38120609560/artifacts/11695646081).

- The source-derived crosswalk contains **193 unique assembly labels** and marks **58 instrumented locations**.
- The generated OpenMC midplane plot and labeled overlay are included in the artifact as radial_mats_midplane.png and beavrs_coordinate_overlay.png.
- Visual inspection shows the crosswalk label centers align with the generated assembly-cell grid; there is no obvious one-bin translation or mesh-extent mismatch in the overlay.
- This is an internal geometry-registration check, not independent confirmation that the experimental detector map uses the same orientation. The red boxes are derived from the same detector-label CSV and crosswalk, so they must still be compared with the published BEAVRS detector-layout schematic.

### Updated interpretation

The plot-only audit reduces concern about a simple mesh-center/extent offset, but it does not explain the poor detector-map agreement. Do **not** select a reflected/rotated map because it yields a better correlation. Next, independently compare the 58 red-box positions with the published detector-layout schematic and review the physical model's state/loading assumptions and the measurement operator. A new high-budget transport run is not justified until that review is recorded.

The BEAVRS spatial-validation claim remains **NOT_ESTABLISHED**; the existing U-235 run's correlation (0.03236) and normalized RMSE (0.32892) are unchanged.


## Independent detector-position and raw-map cross-check — 11 October 2026

The detector label set was independently checked against the pinned upstream model's Core._set_instrument_tube_positions dictionary, rather than inferred only from the generated overlay. The upstream model has **58 unique instrumented assembly labels**; the raw Cycle-1 day-0 detector CSV has **58 unique labels**; their symmetric difference is empty (58/58 exact match). The official BEAVRS specification's Figure 31 lists assembly columns R through A and rows 1 through 15, and its detector layout is consistent with the generated labeled overlay ([BEAVRS v2.0.2 specification, Section 2.2.3.3, Figure 31](https://bpb-us-e1.wpmucdn.com/sites.mit.edu/dist/9/643/files/2017/01/BEAVRS_2.0.2_spec.pdf); [pinned upstream source](https://github.com/mit-crpg/BEAVRS/blob/1ccae04dc3830a5977f08ed7f5f7e1e51ded0d22/models/openmc/beavrs/core.py)). This resolves the detector-label set and makes a simple x/y reflection or one-bin shift an unsupported explanation for the poor result.

The archived U-235 statepoint was also compared against both the raw detector map and the tilt-corrected map, without rerunning transport. Both comparisons use the same 58 calculated values and normalize each measurement subset to mean 1:

| Reference map | Normalized RMSE | Normalized MAE | Mean absolute relative error | Pearson correlation |
|---|---:|---:|---:|---:|
| Raw radial detector map | 0.36212 | 0.30079 | 31.44% | -0.13886 |
| Tilt-corrected radial map | 0.32892 | 0.26960 | 27.75% | 0.03236 |

The tilt-corrected map is descriptively closer, but both comparisons remain poor. The benchmark documentation explicitly notes that the reason for the measured tilt and the validity of the planar tilt correction are not definitive; neither map should be treated as a guaranteed ground truth without its uncertainty context.

### Updated next step

Coordinate registration is now supported by (1) the generated geometry overlay, (2) the official detector-layout diagram, and (3) exact equality between the 58 upstream instrument-tube labels and 58 raw measurement labels. Do not spend another run trying arbitrary coordinate flips. Investigate the physical-model/observable mismatch next: verify the exact Cycle-1 fuel-loading and burnable-absorber states, rod insertion conventions and geometry, and the mapping from chamber-derived measurements to the U-235 tally. Then predeclare a physically justified comparison rule and uncertainty treatment. Physical validation remains **NOT_ESTABLISHED**.
