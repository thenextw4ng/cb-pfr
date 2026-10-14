# CB-PFR HTML Workstation

A lightweight HTML/CSS/JavaScript scientific interface with a local Python API. The interface uses Plotly.js (loaded from its public CDN) for interactive candidate charts and spatial field visualization.

## Run locally

From the repository root:

```bash
python -m pip install -r requirements.txt
python web_server.py
```

Open http://127.0.0.1:8765. Stop the server with Ctrl+C.

The server uses Python's standard library for HTTP, plus the project's `h5py` and `numpy` dependencies to read the archived OpenMC statepoint. For the spatial lab to display real mesh values, the expected ZIP archive must exist in the repository root or on the Desktop path documented above. Plotly.js is loaded from its CDN, so the charts require internet access.

## Visualizations

- Candidate comparison and k-effective distribution from the corrected-group 18-run campaign: `results/c5g7_corrected_group_repeatability_smoke_2026-10-11/fission_objective_repeatability_summary.csv`, validated against `run_level_fission_objective.csv` and `fission_objective_repeatability.json`. The API checks six layouts, three unique seeds/statepoints per layout, corrected MGXS identity, group-structure audit status, and recomputes reported between-seed means/SDs before serving the records. The plotted SD is descriptive across three runs, not a calibrated confidence interval.
- OpenMC spatial tally: 2D heatmap, contour map, and interactive 3D surface from the exact archive member `c5g7-run/2d/statepoint.20000.h5` in `OpenMC_HDF5_Evidence_2026-10-11.zip`.
- Select flux, fission, or nu-fission; choose mean tally or relative Monte Carlo standard deviation; switch between log and linear display for means; select a color scale.
- The API reports SHA-256 and whether the archived statepoint matches `evidence/openmc_local_baseline_2026-10-11/statepoint_summary.json`.

- Assembly-integrated fission-proxy visualizations remain loaded from the separate `results/c5g7_assembly_fission_proxy_smoke_2026-10-11.csv` campaign. These are four discrete, unit-undocumented proxy values with independent seeds; they are not paired with the corrected-group candidate summaries, are not absolute power, and are not interpolated into a continuous field. The current model is not a hexagonal core, so the UI does not fabricate a hex-lattice rendering.

## API

- `GET /api/health` — process health and evidence mode
- `GET /api/candidates` — candidate records and source metadata
- `GET /api/assembly` — four assembly-integrated fission-rate proxy values per recorded candidate
- `GET /api/mesh` — archived 2D OpenMC mesh tallies and provenance metadata. The server checks the repository-root archive first, then `~/Desktop/OpenMC_HDF5_Evidence_2026-10-11.zip` so large evidence need not be committed to GitHub.
- `GET /api/axial-3d?score=flux` — true archived 51 × 51 × 30 OpenMC volume, with input/statepoint/NPZ provenance and selected score. The available high-budget volume is from the separate UMMU run; it is not retargeted when the candidate selector changes and is not a substitute for six-layout validation.

## Scientific limits

- The assembly diagram is a categorical 2×2 schematic from the recorded layout signature; it is not pin-cell geometry.
- Mesh axes use stored physical mesh coordinates when archived bounds are available; otherwise they remain mesh-bin indices. No material identity, assembly placement, or physical core orientation is inferred from the tally alone.
- The 2D planar mesh and true 51 × 51 × 30 axial volume are separate recorded tally sources and are not inferred from candidate-summary numbers or assembly-proxy bins.
- Between-seed sample SD of the three-run derived scalar is descriptive variability, not a calibrated confidence interval or safety margin.
- The fission objective is `max(assembly-integrated fission tally) / mean(assembly-integrated fission tally)`; it is dimensionless, not absolute thermal power, pinwise power, or a reactor-safety metric.
- The composition-only QUBO `E(y) = A(Σyᵢ − 2)²` enforces two MOX positions; all six feasible layouts tie at zero energy and QUBO alone does not select a physical winner. The legacy fresh/once-burned/twice-burned QUBO remains unmapped to this UO₂/MOX C5G7 model.
- No design-specific acceptable k-effective band has been approved. The UI does not launch OpenMC, certify physical feasibility, claim full physical validation, establish confirmatory CB-PFR superiority on physical data, or claim quantum advantage.
- Research dossier: https://github.com/thenextw4ng/cb-pfr/blob/research/cbpfr-four-gate-closeout-2026-10-12/docs/CB-PFR_SIMULATOR_RESEARCH_DOSSIER.md
- Evidence-bounded claims: https://github.com/thenextw4ng/cb-pfr/blob/research/cbpfr-four-gate-closeout-2026-10-12/reports/CBPFR_EVIDENCE_BOUNDED_SCIENTIFIC_CLAIMS_2026-10-12.md
- A–G final closeout: https://github.com/thenextw4ng/cb-pfr/blob/research/cbpfr-four-gate-closeout-2026-10-12/reports/CBPFR_A-G_FINAL_EVIDENCE_CLOSEOUT_2026-10-12.md

The existing Streamlit application remains intact as a fallback while this interface is tested.


## External OpenMC geometry artifacts

The HTML workstation does **not** draw a synthetic assembly map. It discovers and previews existing geometry files from OpenMC/ParaView workflows under these repository folders: `plots/`, `plot/`, `geometry/`, `model/`, `c5g7-run/`, `evidence/`, `results/`, and `artifacts/`.

1. Activate the Python environment that has the OpenMC executable available.
2. Use the validated model input directory containing `geometry.xml`, `materials.xml`, and `settings.xml`.
3. Generate a geometry-only slice plot (this does not run neutron transport):

   ```bash
   python tools/export_openmc_geometry.py --model-dir model
   ```

   Replace `model` with the directory containing the real XML inputs. For the workstation to discover the result, place/copy the resulting `cbpfr_geometry/` directory under one of the scanned repository folders (for example `model/cbpfr_geometry/`).
4. Refresh the HTML workstation and press **Refresh artifacts** in OpenMC geometry explorer.

The helper uses OpenMC `--plot` mode only. It does not modify authoritative XML inputs or run a transport simulation. Its default slice window is 100 cm × 100 cm centered at (0, 0, 0); inspect and adjust plot origin/width in the helper if that does not match the model coordinate bounds.

PNG plots are previewed directly. VTK/VTI files are listed as real 3D datasets and can be opened in ParaView; the dashboard does not pretend that a 2D tally surface is a volumetric reactor geometry.

Official OpenMC geometry visualization guide: https://docs.openmc.org/en/latest/usersguide/plots.html

## Paper figure exports

The Evidence Integrity section includes a **Paper figure export** panel. It exports the current source-backed Plotly chart as a white-background 2200 × 1400 PNG and writes a same-stem JSON sidecar containing the figure identity, selected view settings, available source provenance, and interpretation boundaries.

Export only after selecting the intended metric/score and display mode. Keep the PNG and JSON together. Before publication, inspect the PNG at 100%, confirm labels and coordinate/unit basis, and cross-check the sidecar against raw campaign records. This feature does not improve convergence or turn a diagnostic tally into validation evidence.

See [CB-PFR Paper Figure Export and Caption Guide](../docs/CBPFR_PAPER_FIGURE_EXPORT_GUIDE.md) for recommended source records, caption templates, and limitations.
