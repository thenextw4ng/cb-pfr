# ReactorQ High-Budget Workstation

## Purpose

The Streamlit page `pages/06_High_Budget_Evidence.py` makes the completed C5G7 high-budget study inspectable from inside ReactorQ Studio. It is a data viewer and contract checker; it does not start OpenMC transport.

## Evidence source

- Workflow: https://github.com/thenextw4ng/cb-pfr/actions/runs/38182056526
- Artifact: `cbpfr-c5g7-high-budget-complete-2026-10-12` (raw HDF5 statepoints and full audit outputs)
- Committed compact UI dataset: `results/c5g7_high_budget_2026-10-12/run_level_evidence.json`
- Source commit recorded by the study: `ba41bee54320ada0b4ac39a0dd2ca3c1d090a450`

## Contract checked by the page

The viewer checks the 18-run / six-layout / three-runs-per-layout structure, unique seeds, unique statepoint SHA-256 values, one shared MGXS SHA-256, corrected-group audit labels, common compute settings, expected group boundaries, finite metrics, and explicit flags that physical validation, convergence certification, and winner selection are not approved.

## Interpretation limits

The plotted 95% intervals are descriptive two-sided Student-t intervals across only three independent seed runs per layout (two degrees of freedom). They are not proof of convergence or physical superiority. The reported fission-rate peaking factor is a proxy from the current model, and all displayed results remain subject to model and tally-mapping review. No safety or design-approval conclusion is supported.

## Run locally

```bash
pip install -e .
pip install -r requirements-dashboard.txt
streamlit run app.py
```

Open **High-Budget Evidence** from the custom project sidebar.
