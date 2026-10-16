# CB-PFR HTML Workstation

Use the API-backed local server to enable the restored OpenMC spatial visualizations. Do not use `python3 -m http.server`: that serves static files only and cannot provide the statepoint/geometry API.

From the repository root:

```bash
python3 -m pip install h5py numpy
python3 web_server.py
```

Then open http://127.0.0.1:8765. Keep the terminal open while using the workstation; press Ctrl+C to stop it.

## Restored views

- Archived-statepoint mesh: 2D heatmap, labeled contour, central-row profile, and interactive Plotly 3D surface.
- Mesh score selector (flux, fission, nu-fission), mean/relative Monte Carlo SD, log/linear display for means, and color-scale control.
- Geometry-artifact explorer scans allowed repository folders for existing OpenMC plots and VTK/VTI datasets.
- Latest 16 Oct 2026 campaign replay and the revised-paper T2/T3/T7/T7b evidence remain in the separate Experiments & paper section.

The 3D tally surface is a surface representation of the recorded 2D tally, not a volumetric reactor solution. Geometry previews use existing OpenMC/ParaView artifacts; missing geometry is never fabricated.

Expected statepoint archive: `OpenMC_HDF5_Evidence_2026-10-11.zip` in the repository root, containing `c5g7-run/2d/statepoint.20000.h5`. This archive is tracked in the repository.
