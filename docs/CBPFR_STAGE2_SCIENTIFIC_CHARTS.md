# CB-PFR Simulator — Stage 2 Scientific Chart Redesign

## Scope

Stage 2 uses scientific views while preserving the existing HTML workstation structure, Core Geometry Explorer, Plotly.js runtime, and OpenMC spatial tally views. This sync revision binds candidate metrics to the corrected-group 18-run research campaign rather than the older one-run candidate smoke summary.

## Implemented views

### Candidate comparison — point-range plot
- Plotly scatter marks show each candidate's recorded metric against its layout signature.
- For `keff_mean`, the horizontal error bar is the between-seed sample SD of the derived layout mean across three independent smoke runs; it is not a confidence interval. Missing values are not inferred.
- The metric selector also supports the mean dimensionless fission-rate peaking factor, with its between-seed sample SD from the same three-run layout campaign.
- A dashed `k_eff = 1` line is labelled **reference only**. It is not a safety criterion, feasibility certificate, or ranking threshold.
- Selecting a candidate highlights its point. Alternative flux/fission score selections remain available, but are not given invented uncertainty intervals.

### Ranked k-effective candidates — dot plot
- The six recorded candidate means are sorted from low to high and displayed as individual observations; no histogram binning is applied.
- Between-seed sample SD values are shown as vertical spread indicators; tooltips explicitly identify these as between-seed SD, not within-run Monte Carlo standard error or a calibrated confidence interval.
- Candidate layout labels remain horizontal, hover data retain candidate ID, layout, seed, mean, and reported SD, and `k_eff = 1` remains an explicitly interpretive reference.
- Candidate selection is highlighted in this plot as well as in the comparison plot.

### Physics-metric trade-off — scatter plot
- The corrected-group mean k-effective is plotted against the mean fission-rate peaking proxy, both calculated from the same three-run candidate summary.
- Error bars show the between-seed sample SD on each axis; hover preserves the candidate ID, layout, three seeds, and descriptive proxy rank.
- The dimensionless objective is max(assembly-integrated fission tally) / mean(assembly-integrated fission tally); it is not absolute power or a reactor-safety metric.
- The scatter is a descriptive trade-off only. It is not a physical feasibility ranking or winner certificate, and the k-effective reference line remains interpretive only.

### Candidate-by-position proxy matrix
- A single Cividis heatmap contains the recorded `p00_fission_rate`, `p01_fission_rate`, `p10_fission_rate`, and `p11_fission_rate` values, shown as P00–P11 columns and candidate layout rows.
- The shared color range is computed from the displayed, finite source values. Numeric cell labels are rounded for readability; hover preserves the recorded value and proxy seed.
- The selected candidate row is outlined. Its 2 × 2 selected-candidate spatial map remains available as a separate view.
- Records are joined by exact candidate ID **and** layout signature. No value is borrowed from a different candidate to fill a gap.
- Proxy seeds are independent of the candidate-summary seeds. This matrix is descriptive proxy evidence, not a paired-run comparison or absolute-power map.

## Source and limits

The candidate plots use `results/c5g7_corrected_group_repeatability_smoke_2026-10-11/fission_objective_repeatability_summary.csv`, cross-checked against the 18 rows in `run_level_fission_objective.csv` and `fission_objective_repeatability.json`. The server fails closed if the run counts, unique seeds/statepoint hashes, corrected MGXS hashes, group-structure audits, or recomputed means/SDs disagree.
The four-position map uses `results/c5g7_assembly_fission_proxy_smoke_2026-10-11.csv`, a separate exploratory campaign with independent seeds. Those discrete observations are not paired with the candidate study and their physical units are undocumented.

The composition-only QUBO `E(y)=A(Σᵢyᵢ−2)²` enforces two MOX positions but gives all six feasible layouts equal zero energy; it does not encode physical performance. The legacy burnup-state formulation is not mapped to this C5G7 composition case. No design-specific acceptable k-effective band has been approved, so no layout is declared a winner.
The dashboard does not run OpenMC, interpolate the four assembly proxy values into a continuous field, manufacture missing records, or claim physical validation, physical-data superiority of CB-PFR, or quantum advantage.

## Verification targets

The Node candidate UI tests and Playwright browser smoke test check:
- Six actual candidate observations and SD intervals in both k-effective plots.
- The reference-only `k_eff = 1` annotations.
- Separate flux/fission axes with one scatter trace.
- A six-row, four-position matrix preserving exact source proxy values and selected-row synchronization.
- Preservation of Stage 1 core-geometry checks and all four OpenMC spatial tally views.
- Responsive desktop/mobile layout and uncaught browser error checks.
