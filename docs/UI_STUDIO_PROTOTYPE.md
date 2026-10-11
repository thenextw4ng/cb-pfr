# ReactorQ Studio — UI prototype

This branch adds an alternative Streamlit interface in `app_studio.py` without replacing the existing `app.py`.

## Run locally

```bash
python -m pip install -r requirements-dashboard.txt
streamlit run app_studio.py
```

## UI principles

- Evidence-first: displays committed corrected-group run-level CSV data rather than inventing reactor outputs.
- Explicit uncertainty and validation states: smoke-study findings remain exploratory; no layout is recommended.
- Scientific provenance: exposes seed rounds, statepoint hashes, MGXS hashes, and group-structure audit status.
- Separation of models: the legacy burnup-state QUBO is not represented as a validated mapping to the C5G7 UO2/MOX layout study.
- Additive change: the existing dashboard and project workflow remain untouched.

## Current limitations

The dashboard is an analysis and reporting interface. It does not launch OpenMC, edit geometry/materials, execute QUBO optimization, or establish benchmark-grade convergence. It reads the corrected-group smoke-study CSV committed in this repository.
