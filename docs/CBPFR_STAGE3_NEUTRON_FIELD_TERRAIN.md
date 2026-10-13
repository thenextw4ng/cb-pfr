# CB-PFR Simulator — Stage 3: Neutron-Field Terrain

## Scope

Stage 3 refines only the existing Plotly.js surface within the HTML workstation's Spatial Field Laboratory. It retains the archived OpenMC mesh as the sole numeric source. It does not generate a new field, run OpenMC, or add a volumetric transport solver.

## Surface rendering

- The selected recorded 2D mesh is drawn as an interactive surface, with improved directional lighting, shading, and a dark technical scene background.
- Up to six Z isoline levels are computed from the observed selected-field range using marching-squares segments and drawn as 3D line overlays on the surface and projected to the lower reference plane. Bounding the line levels keeps interactive redraw responsive while preserving the recorded field as the only source; the coordinated 2D contour plot retains its own field-derived interval.
- The projected lines are a visual aid for reading topology; they are not another tally or a physical reactor boundary.
- X/Y axes use the archived regular-mesh lower/upper bounds in cm and cell-centre coordinates when the API says those coordinates are available. Otherwise the labels explicitly remain zero-based mesh-bin indices.
- The camera is initialized to a documented default, remains user-interactive, and can be reset with the surface-panel button.
- Scene aspect ratio retains the relative X/Y extent of the recorded mesh.

## Vertical exaggeration

The UI offers 1×, 1.5×, 2×, and 3× display exaggeration settings. These change only the Plotly scene aspect ratio. They do **not** multiply, offset, interpolate, or replace any Z matrix value or hover payload. This avoids changing source data merely to produce a more dramatic-looking surface.

The selected tally score, mean/relative-standard-error view, linear/log display scale, and colour palette continue to apply to the coordinated heatmap, contour, profile, and surface. Log display transforms the plotted Z/colour coordinate as `log10(mean)` for positive mean bins; hover continues to report the recorded tally mean and Monte Carlo uncertainty values.

## Hover semantics

Surface, heatmap, and contour hover payloads retain:
- Recorded tally mean for the selected score.
- Stored Monte Carlo standard error (the API's `standard_error`, with backward-compatible `std_dev` fallback).
- Relative Monte Carlo standard error (%) derived only for positive means.
- Physical cell-centre X/Y coordinates in cm where archived bounds are verified, else explicit mesh-bin indices.
- The displayed Z value when relevant (for example, `log10(mean)`) so the view transform is not confused with the source tally.

## Verification

The Playwright browser smoke test asserts that:
- The 3D plot contains the full 51×51 mesh.
- Surface contours are enabled and projected to the lower reference plane.
- Physical X/Y titles are used when archived bounds exist.
- Each inspected point carries source mean, Monte Carlo standard error, and relative error.
- Selecting 3× changes the scene aspect ratio but leaves the selected source `z` value and hover payload unchanged.
- Reset camera restores the expected eye position.
- All previous candidate, Core Geometry Explorer, spatial heatmap/contour/profile/surface, and desktop/mobile checks remain in the workflow.

## Scientific boundary

A 2D mesh tally visualized as a 3D surface is not a 3D neutron-transport solution. The plotted Z axis is the chosen tally/uncertainty display field, not physical reactor height. A projected contour is only a display aid. No artificial peaks, smoothing, or interpolated cells are inserted. No physical validation is claimed.
