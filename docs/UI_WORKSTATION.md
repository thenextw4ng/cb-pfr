# CB-PFR Research Workstation UI

This branch adds an evidence-linked Streamlit multipage interface.

## Run locally

From the repository root:

```bash
python -m pip install -r requirements-dashboard.txt
streamlit run app.py
```

Streamlit automatically discovers the pages in `pages/` and lists them in the sidebar.

## Pages

- `01_C5G7_Layout_Explorer.py`: interactive selector and schematic for the repository's explicit four-position C5G7 UO2/MOX layout study. Values are loaded from the committed smoke-run CSV.
- `02_Physics_Field_Explorer.py`: inventories available aggregate fields and states the requirements for cell-wise flux/fission/power maps. It deliberately does not fabricate spatial data.
- `03_Monte_Carlo_Reliability.py`: shows recorded smoke-run values and their actual run settings. These are exploratory, not benchmark-grade rankings.
- `04_QUBO_Optimization.py`: enumerates all 16 binary assignments and identifies the six exact-two-MOX feasible layouts for the separate C5G7 design QUBO.
- `05_Provenance_Validation.py`: evidence status, run identifiers, hashes, and the outstanding scientific validation gates.

## Scientific presentation rules

- Every displayed result must be traceable to a committed result file or explicitly labelled as a schematic/demo.
- Aggregate scores must not be represented as spatial fields.
- OpenMC statepoint readability and passing software tests do not prove benchmark validation.
- The legacy burnup-state QUBO is not mapped to UO2/MOX without a defensible, source-backed physical mapping.
- Smoke-run results must not be used to declare a winning layout.

## Scope

The four-position assembly-placement visualization is intentionally **not** a full-core C5G7 geometry reconstruction. Cell-wise field views should be added only after the UI loads the audited statepoint tally arrays and preserves mesh dimensions, score units, uncertainty, settings, and statepoint provenance.
