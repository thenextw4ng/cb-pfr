# ReactorQ Studio (MVP)

A small dashboard for inspecting the existing abstract QUBO + CB-PFR research pipeline and checking OpenMC runtime/model readiness.

## Quick start

Python 3.10+ recommended.

```bash
git clone https://github.com/thenextw4ng/cb-pfr.git
cd cb-pfr
git checkout integration/reactorq-studio
python -m venv .venv
source .venv/bin/activate
pip install -e .
pip install -r requirements-dashboard.txt
streamlit run app.py
```

The dashboard opens locally in your browser.

## Modes

- **Synthetic demo:** creates an abstract seven-position QUBO fixture, ranks a subset of feasible candidates with all four existing comparison methods, and exports CSV/JSON. All generated estimates are explicitly labelled synthetic.
- **OpenMC preflight:** checks for an OpenMC executable, `OPENMC_CROSS_SECTIONS`, and the required model XML files. This is only a readiness check; it does not launch OpenMC.

## Important scientific boundary

This repository currently does not provide a defensible mapping from the abstract labels `fresh`, `once_burned`, and `twice_burned` to actual OpenMC materials/compositions. The app therefore does not fabricate geometry/materials or claim a physical run. A validated benchmark model, nuclear data, mapping, tallies, and independent reference protocol are required before physical metrics can be reported.

## Outputs

- `reactorq_rankings.csv`: per-method candidate ranking with provenance labels.
- `reactorq_experiment.json`: ranking records and run metadata.

## Status

Research MVP; not reactor design software, a safety tool, or a physical validation certificate.
