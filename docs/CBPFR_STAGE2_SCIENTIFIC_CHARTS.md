# CB-PFR Simulator — Stage 2 Scientific Chart Redesign

## Scope

Stage 2 replaces generic candidate histograms and grouped bars with scientific views while preserving the existing HTML workstation structure, Stage 1 Core Geometry Explorer, Plotly.js runtime, and OpenMC spatial tally views.

## Implemented views

### Candidate comparison — point-range plot
- Plotly scatter marks show each candidate's recorded metric against its layout signature.
- For `keff_mean`, the horizontal error bar is populated from the matching record's `keff_std_dev`; missing values are not inferred.
- A dashed `k_eff = 1` line is labelled **reference only**. It is not a safety criterion, feasibility certificate, or ranking threshold.
- Selecting a candidate highlights its point. Alternative flux/fission score selections remain available, but are not given invented uncertainty intervals.

### Ranked k-effective candidates — dot plot
- The six recorded candidate means are sorted from low to high and displayed as individual observations; no histogram binning is applied.
- Reported `keff_std_dev` values are shown as vertical error bars.
- Candidate layout labels remain horizontal, hover data retain candidate ID, layout, seed, mean, and reported SD, and `k_eff = 1` remains an explicitly interpretive reference.
- Candidate selection is highlighted in this plot as well as in the comparison plot.

### Aggregate score relationship — scatter plot
- `aggregate_flux_score` is plotted on the X-axis and `aggregate_fission_score` on the Y-axis.
- The two repository scores are not combined on a common scale. Axes explicitly state that source units are unspecified.
- Hover content retains candidate ID, layout signature, and seed. The selected candidate is highlighted.
- These aggregate values remain scores, not absolute flux, power, or a physical-feasibility conclusion.

### Candidate-by-position proxy matrix
- A single Cividis heatmap contains the recorded `p00_fission_rate`, `p01_fission_rate`, `p10_fission_rate`, and `p11_fission_rate` values, shown as P00–P11 columns and candidate layout rows.
- The shared color range is computed from the displayed, finite source values. Numeric cell labels are rounded for readability; hover preserves the recorded value and proxy seed.
- The selected candidate row is outlined. Its 2 × 2 selected-candidate spatial map remains available as a separate view.
- Records are joined by exact candidate ID **and** layout signature. No value is borrowed from a different candidate to fill a gap.
- Proxy seeds are independent of the candidate-summary seeds. This matrix is descriptive proxy evidence, not a paired-run comparison or absolute-power map.

## Source and limits

The candidate plots use `results/c5g7_layout_smoke_2026-10-10/candidate_summary.csv`. The position matrix and selected-candidate 2 × 2 map use `results/c5g7_assembly_fission_proxy_smoke_2026-10-11.csv`. They are different recorded evidence products with different run seeds and are not silently treated as paired observations.

Stage 2 does not run OpenMC, interpolate four assembly proxy values into a continuous field, manufacture values for missing records, or claim physical validation.

## Verification targets

The Node candidate UI tests and Playwright browser smoke test check:
- Six actual candidate observations and SD intervals in both k-effective plots.
- The reference-only `k_eff = 1` annotations.
- Separate flux/fission axes with one scatter trace.
- A six-row, four-position matrix preserving exact source proxy values and selected-row synchronization.
- Preservation of Stage 1 core-geometry checks and all four OpenMC spatial tally views.
- Responsive desktop/mobile layout and uncaught browser error checks.
