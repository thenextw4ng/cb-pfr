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
