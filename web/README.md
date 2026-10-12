# CB-PFR HTML Workstation

A lightweight HTML/CSS/JavaScript scientific interface with a local Python API. The interface uses Plotly.js (loaded from its public CDN) for interactive candidate charts and spatial field visualization.

## Run locally

From the repository root:

```bash
python -m pip install -r requirements.txt
python web_server.py
```

Open http://127.0.0.1:8765. Stop the server with Ctrl+C.

The server uses Python's standard library for HTTP, plus the project's `h5py` and `numpy` dependencies to read the archived OpenMC statepoint. Plotly.js is loaded from its CDN, so the charts require internet access.

## Visualizations

- Candidate comparison, recorded k-effective distribution, and aggregate flux/fission scores from `results/c5g7_layout_smoke_2026-10-10/candidate_summary.csv`.
- OpenMC spatial tally: 2D heatmap, contour map, and interactive 3D surface from the exact archive member `c5g7-run/2d/statepoint.20000.h5` in `OpenMC_HDF5_Evidence_2026-10-11.zip`.
- Select flux, fission, or nu-fission; choose mean tally or relative Monte Carlo standard deviation; switch between log and linear display for means; select a color scale.
- The API reports SHA-256 and whether the archived statepoint matches `evidence/openmc_local_baseline_2026-10-11/statepoint_summary.json`.

- Assembly-level 2 × 2 heatmap and bar comparison from `results/c5g7_assembly_fission_proxy_smoke_2026-10-11.csv`; the source is explicitly marked exploratory smoke evidence and is not absolute power. The current model is not a hexagonal core, so the UI does not fabricate a hex-lattice rendering.

## API

- `GET /api/health` — process health and evidence mode
- `GET /api/candidates` — candidate records and source metadata
- `GET /api/assembly` — four assembly-integrated fission-rate proxy values per recorded candidate
- `GET /api/mesh` — archived 2D OpenMC mesh tallies and provenance metadata

## Scientific limits

- The assembly diagram is a categorical 2×2 schematic from the recorded layout signature; it is not pin-cell geometry.
- Mesh axes are bin indices only. No material identity, assembly coordinates, or physical orientation are inferred.
- The 3D visualization is a surface representation of the recorded 2D field, not a true volumetric reactor mesh.
- Relative SD is computed as 100 × standard deviation / mean for positive finite means only.
- Flux, fission, and nu-fission scores are not automatically absolute thermal power in watts.
- The UI does not launch OpenMC, prove physical feasibility, or certify a reactor design.
- QUBO-to-C5G7 mapping and CB-PFR physical validation remain unresolved/not established in the repository evidence.

The existing Streamlit application remains intact as a fallback while this interface is tested.
