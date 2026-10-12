# CB-PFR HTML Workstation

A lightweight HTML/CSS/JavaScript front end with a Python standard-library API. It reads the checked-in candidate summary and explicitly labels the interface as recorded-evidence-only. It does **not** run OpenMC, prove physical feasibility, or fabricate missing spatial fields.

## Run locally

From the repository root:

```bash
python web_server.py
```

Open http://127.0.0.1:8765. Stop the server with Ctrl+C.

The server uses only Python's standard library. Plotly.js is loaded from its public CDN, so charts require internet access. Candidate records are read from `results/c5g7_layout_smoke_2026-10-10/candidate_summary.csv`.

## API

- `GET /api/health` — process health and evidence mode
- `GET /api/candidates` — candidate records plus source metadata

## Scientific limits

- The assembly diagram is a categorical 2×2 schematic from the recorded layout signature; it is not pin-cell geometry.
- k-effective and aggregate scores are displayed as recorded. Score units are not inferred.
- Aggregate candidate scores are not spatial fields.
- The separately archived 51×51 OpenMC mesh tally is not reconstructed by this MVP.
- QUBO-to-C5G7 mapping and CB-PFR physical validation remain unresolved/not established per the repository evidence matrix.

The existing Streamlit application remains intact as a fallback while the HTML interface is tested.
