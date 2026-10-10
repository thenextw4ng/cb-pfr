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

## Repeated-run consistency analysis

The package also exposes `cbpfr.repeatability.summarize_repeated_rankings(runs, top_k=1)` for post-processing ordered candidate IDs from independent optimizer runs. It reports top-1 selection frequency, top-k selection frequency, top-1 dominance, and mean pairwise Jaccard overlap of top-k candidate sets. The Jaccard score compares set membership, not rank positions. With only one run, pairwise overlap is defined as 1.0 by convention and should not be interpreted as observed cross-run stability. These are descriptive repeatability measures only: they do not certify a global optimum or physical validity.
