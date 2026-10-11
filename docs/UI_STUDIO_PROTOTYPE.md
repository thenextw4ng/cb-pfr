# ReactorQ Studio — visual scientific workbench

This branch adds an alternative Streamlit interface in `app_studio.py` without replacing the existing `app.py`.

## Run locally

```bash
python -m pip install -r requirements-dashboard.txt
streamlit run app_studio.py
```

## What the interface now includes

- **Reactor map:** interactive 2×2 UO₂/MOX assembly-placement schematic for the selected candidate.
- **Four-position tally view:** heatmap of the actual recorded `R_p00`–`R_p11` values for a selected run.
- **Spatial tally viewer:** upload a real OpenMC mesh-tally CSV with numeric `x`, `y`, and `value` columns to render a 2D heatmap.
- **Physics results:** interactive per-run k-effective trend, fission-rate peaking-proxy distribution, and layout comparison plots.
- **Layout lab:** candidate comparison and replicate summaries.
- **Run provenance:** filters, run-level scatter plot, hashes, and CSV export.
- **Validation gates:** explicit distinction between available evidence and unresolved scientific validation.

## Scientific integrity

The committed run-level CSV powers the layout and run charts. The 2×2 tile diagram is a material-placement abstraction, **not** a pin-resolved reactor geometry. The four-position heatmap is the recorded position-contribution proxy, **not** a full-core neutron-flux or absolute-power map. A spatial field is rendered only from user-supplied OpenMC tally data; the app does not fabricate missing flux/power values.

## Limitations

The dashboard does not launch OpenMC, edit geometry/materials, or execute QUBO optimization. Current committed results are a low-budget smoke study, not benchmark-grade validation, a safety assessment, or a design recommendation. The legacy burnup-state QUBO is not represented as a validated mapping to the C5G7 UO₂/MOX layout study.

The existing `app.py` and `main` branch are unchanged by this prototype.
