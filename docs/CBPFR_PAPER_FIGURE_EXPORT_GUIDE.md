# CB-PFR Simulator — Paper Figure Export and Caption Guide

## Purpose

Use the dashboard's **Paper figure export** controls to render individual source-backed Plotly views on a white background. Each export should produce:
- a high-resolution PNG (4400 × 2800 pixels); and
- a JSON sidecar with plot identity, export settings, selected metric/view, available provenance, and interpretation boundaries.

Keep the PNG and same-stem JSON sidecar together in the paper's figure directory. These files help prepare reproducible figures; they do not replace raw data, uncertainty definitions, simulation settings, or validation limitations in the manuscript.

## Recommended manuscript figures

### Figure 1 — Method workflow (prepare as a dedicated vector diagram)

Show: candidate encoding / QUBO → structural feasibility check → OpenMC transport → tally and uncertainty extraction → CB-PFR screening/ranking → evidence report. Explicitly note that the current composition-only QUBO enforces exactly two MOX assignments but gives all six feasible layouts the same zero penalty. Do not depict QUBO alone as the physical optimizer or call it quantum-hardware execution unless a QPU job is documented.

### Figure 2 — Corrected-group k-effective by candidate

Dashboard export: **Export · k-effective** (distributionChart).

Caption template:

> Mean effective multiplication factor for the six feasible C5G7 UO₂/MOX layouts in the corrected-group exploratory campaign. Points denote the mean of three independent seed runs per layout; error bars denote between-seed sample standard deviation, not a calibrated confidence interval. This smoke-budget comparison is descriptive and does not establish a physically acceptable layout or a converged winner.

Source records:
- results/c5g7_corrected_group_repeatability_smoke_2026-10-11/fission_objective_repeatability_summary.csv
- results/c5g7_corrected_group_repeatability_smoke_2026-10-11/run_level_fission_objective.csv
- results/c5g7_corrected_group_repeatability_smoke_2026-10-11/fission_objective_repeatability.json

Do not remove the uncertainty definition or treat the point spread as an interval estimate with nominal coverage.

### Figure 3 — k-effective versus dimensionless fission-rate peaking proxy

Dashboard export: **Export · Metric trade-off** (aggregateChart).

Caption template:

> Descriptive relationship between candidate mean k-effective and the dimensionless relative assembly-integrated fission-rate peaking proxy, computed from the same corrected-group 18-run campaign. Uncertainty marks indicate between-seed sample variability. The proxy is not absolute power, pin-wise power, a thermal-hydraulic metric, or a reactor-safety limit; no approved design-specific acceptance band is applied.

Source records: the same three corrected-group campaign files as Figure 2. This chart is descriptive; it does not prove causality, feasibility, or superiority of CB-PFR.

### Figure 4 — Four-position assembly-proxy map (optional / supplementary)

Dashboard export: **Export · Position map** (assemblyMap) or **Export · Candidate matrix** (assemblyMatrix).

Caption template:

> Four discrete assembly-integrated fission-proxy observations at P00, P01, P10, and P11, displayed in row-major core-position order. The source CSV does not document physical units or absolute-power normalisation. The observations belong to a separate exploratory campaign with independent seeds and must not be interpreted as paired replicates of the corrected-group candidate runs. No interpolation between the four positions is implied.

Source file: results/c5g7_assembly_fission_proxy_smoke_2026-10-11.csv.

Use this only if the proxy-map interpretation adds value to the paper. Do not write “power distribution” without qualifying the proxy and its undocumented unit.

### Figure 5 — Recorded planar OpenMC tally (heatmap / contour / central-row profile)

Dashboard exports: **Export · Heatmap**, **Export · Contour field**, or **Export · Central-row profile**.

Caption template:

> Recorded 51 × 51 planar OpenMC mesh tally for the selected score. Coordinates use archived physical mesh metadata when present; otherwise the display must be described in mesh-bin indices. The heatmap, contour plot, profile, and 3D terrain view are coordinated representations of the same planar tally and are not independent observations. When a logarithmic display is selected, colour encodes the log-transformed positive recorded means while source hover/provenance retains recorded means and Monte Carlo uncertainty. Missing/non-positive bins are not manufactured or filled.

The tally score's units and normalisation must be copied from verified source metadata; do not infer them from the colourbar label alone. Use the sidecar provenance and backend source audit to identify the exact archived statepoint/tally. The 3D surface export is a visual rendering of a 2D field, not a 3D transport result.

### Figure 6 — Axial 3D tally volume (only when it serves a specific purpose)

Dashboard export: **Export · Axial volume** (axial3dPlot).

Before use, inspect the companion JSON sidecar and dashboard run-budget / relative-error diagnostic. The current local screenshot has the explicit **SMOKE DIAGNOSTIC ONLY · HIGH RELATIVE RSE** status; that view may illustrate software rendering capability, but **must not be presented as converged physical evidence or as validation**. If the recorded volume is diagnostic smoke data, say so in the figure title or caption. A high-budget production artifact and a smoke diagnostic are different datasets; never silently substitute one for the other.

## QUBO and interpretation note

For the current composition-only objective,

$$
E(y)=A\left(\sum_{i=1}^{4}y_i-2\right)^2,\qquad A>0,
$$

all six feasible two-MOX/two-UO₂ layouts have E = 0. The plot exports cannot make this QUBO objective physically discriminative. Keep that limitation visible in the paper narrative.

## Export workflow

1. Load the dashboard and wait for the intended chart to render.
2. Select the target metric, tally score, mean/error view, display scale, palette, and axial slice before exporting.
3. Navigate to **Data provenance → Paper figure export** and select the matching figure button.
4. Save the PNG and same-stem JSON sidecar together. Do not rename them independently; if renamed, preserve the association.
5. Open the PNG at 100% and check title, tick labels, colourbar, annotation clipping, positive/missing-bin behaviour, and axis-coordinate units.
6. Use the JSON sidecar to draft the caption, then cross-check every number and run setting against the campaign CSV / JSON / HDF5 evidence. Cite source files and include the uncertainty definition in the paper caption or Methods.
7. Freeze the selected source revision and record the software commit SHA in the manuscript reproducibility statement.

## Limits of the export feature

The export creates a styled raster image and provenance/interpretation sidecar from the current displayed plot. It does not create independent statistical analyses, add missing units, repair convergence, certify spatial coordinates, validate a reactor model, or automatically make the image publication-ready. The author remains responsible for checking source identity, caption, readability, and evidence boundaries.
