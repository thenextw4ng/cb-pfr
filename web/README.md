# CB-PFR HTML Scientific Workstation

The workstation restores the source-linked 3D core geometry explorer, recorded OpenMC spatial views, true axial tally volume, and latest experiments/paper evidence.

## Run locally

From the repository root:
```bash
python3 -m pip install h5py numpy
python3 web_server.py
```
Open http://127.0.0.1:8765. Keep the terminal running; press Ctrl+C to stop. Do not use `python3 -m http.server`: the visualizations rely on the local OpenMC evidence API.

## Visualizations

- **Core Geometry Explorer** — Three.js 3 × 3 C5G7 core material extrusion with orbit/zoom, interactive assembly selection, MOX/UO₂ composition, and source-universe 17 × 17 pin maps.
- **Spatial field lab** — archived tally heatmap, contour, central-row profile, and interactive 3D surface.
- **Physical axial 3D tally** — separate recorded 51 × 51 × 30 OpenMC volume with score, axial slice, opacity, palette, and uncertainty controls. The volume is from the recorded UMMU high-budget run, seed 640000; it is not six-layout validation or absolute power.
- **Experiments & paper** — current 16 October 2026 V2a campaign replay, T2/T3 synthetic benchmarks, and revised T7/T7b paper tables, all loaded from `web/research_snapshot.json`.

## Key evidence

- `evidence/c5g7_openmc_geometry_manifest_2026-10-13.json` — XML-derived core lattice/pin-universe source manifest.
- `evidence/cbpfr_axial_3d/axial_tally_3d.npz` — recorded axial volume; expected SHA-256 `3657af9ffddceb303827c700fa0e6fce5432d655843864b12dd428b6c4c499e4`.
- `OpenMC_HDF5_Evidence_2026-10-11.zip` — recorded statepoint source for the planar tally.
- `web/research_snapshot.json` and `web/RESEARCH_DATA_CROSSWALK_2026-10-16.md` — latest experiments/paper snapshot and crosswalk.

## Scientific boundaries

The 3D core view is a geometry/material-derived schematic extrusion, not an axial transport solution. The axial tally volume is real recorded multi-layer data but is from one UMMU high-budget run and does not establish physical optimality, candidate-specific axial validation for all six layouts, or reactor safety. The planar tally, axial volume, V2a run summaries, and synthetic paper regimes are separate evidence sources.

## Evidence Control Room · Stage 0/1

The Evidence Control Room uses `GET /api/evidence-index` to catalogue the existing corrected-group candidate study, XML-derived core geometry manifest, planar OpenMC statepoint, separate axial OpenMC volume, exploratory assembly proxy, latest V2a policy replay, and synthetic method-paper results. Cards display exact source paths, hash information where available, run metadata, source status, and a link to the relevant workspace section. The registry is metadata-first: it does not pull the full axial array merely to show provenance, merge separate evidence classes, or convert source/hash checks into physical validation.

Stage 0 regression tests protect the 3D core viewer, SVG source map, planar heatmap/contour/profile/surface, axial-volume controls, local evidence APIs, and snapshot separation. The browser visual-smoke job emits desktop/mobile screenshots as build artifacts for review; screenshots are evidence for manual visual comparison, not an automatic pixel-perfect equivalence claim.


## Stage 2 · Interactive 3D Physics Lab

The recorded axial OpenMC tally is shared with `web/axial_investigation.js` through a reference to the API payload already used by the 3D volume viewer. It supplies XY (normal Z), XZ (normal Y), and YZ (normal X) heatmap slices, plus a selectable X/Y/Z line profile with two fixed source-bin indices. Hover/click inspection displays the source mean, standard error, relative standard error, integer bin indices and physical cell-centre coordinates. Mean slices use log10(mean) for colour; line profiles retain the raw mean on a logarithmic y-axis. Relative-error views use the recorded percentage directly. No interpolation, synthetic volume, or geometry overlay is generated.

## Stage 3 · Uncertainty & Comparative Analysis Lab

The comparison panels read `web/research_snapshot.json`:
- V2a layout means and between-run SD for `F_fission` and `k-effective`, with the separate 60-run high-budget empirical F_fission references.
- Equal-budget empirical-best match rates and regret differences vs the point-estimate baseline, using only the interval bounds recorded in the snapshot.
- A separate T7 synthetic-method chart comparing point-estimate, CB-PFR z=1, and adaptive R&S + CB-PFR z*, plus the reported T7b matched-feasibility intervals.

Match-rate confidence intervals are not present in the recorded snapshot, so none are drawn. Error bars on run summaries are between-run SD, not confidence intervals. The high-budget reference is empirical and source convergence remains uncertified. T7/T7b remain synthetic method evidence and are not mixed with OpenMC transport results.
