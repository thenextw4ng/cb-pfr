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
- **OpenMC preflight:** checks for an OpenMC executable, `OPENMC_CROSS_SECTIONS`, and the presence/readability/basic XML well-formedness of the cross-section index plus required model XML files. This is only a shallow readiness check; it does not run OpenMC, validate XML semantics against a specific OpenMC version, check geometry overlap, prove convergence, or validate physics.

## Important scientific boundary

This repository currently does not provide a defensible mapping from the abstract labels `fresh`, `once_burned`, and `twice_burned` to actual OpenMC materials/compositions. The app therefore does not fabricate geometry/materials or claim a physical run. A validated benchmark model, nuclear data, mapping, tallies, and independent reference protocol are required before physical metrics can be reported.

## Outputs

- `reactorq_rankings.csv`: per-method candidate ranking with provenance labels.
- `reactorq_experiment.json`: ranking records and run metadata.

## Status

Research MVP; not reactor design software, a safety tool, or a physical validation certificate.

## Repeated-run consistency analysis

The package also exposes `cbpfr.repeatability.summarize_repeated_rankings(runs, top_k=1)` for post-processing ordered candidate IDs from independent optimizer runs. It reports top-1 selection frequency, top-k selection frequency, top-1 dominance, and mean pairwise Jaccard overlap of top-k candidate sets. The Jaccard score compares set membership, not rank positions. With only one run, pairwise overlap is defined as 1.0 by convention and should not be interpreted as observed cross-run stability. These are descriptive repeatability measures only: they do not certify a global optimum or physical validity.

The dashboard's **Repeatability** tab accepts a JSON array of ordered candidate-ID lists, one list per independent run, and exports the computed summary as `reactorq_repeatability.json`. It analyzes supplied run rankings; it does not launch repeated optimizer runs. The default entries are illustrative examples and must be replaced with actual recorded runs for research analysis.

## Command-line repeatability analysis

For reproducible post-processing outside the dashboard, create a JSON file with one ordered candidate list per recorded optimizer run:

```json
{
  "evidence_kind": "optimizer_recorded_runs",
  "top_k": 3,
  "runs": [
    {"run_id": "seed-11", "candidate_ids_ranked": ["candidate-A", "candidate-B", "candidate-C"]},
    {"run_id": "seed-12", "candidate_ids_ranked": ["candidate-B", "candidate-A", "candidate-D"]}
  ]
}
```

Run:

```bash
python scripts/analyze_repeatability.py --input results/optimizer_runs.json --output results/repeatability_summary.json
```

The output path must not already exist; use a new path for each analysis. Keep the original per-run outputs and record optimizer name/version, parameter settings, seed, stopping condition, candidate feasibility, and any physical-simulation linkage separately. Candidate IDs must identify the same configuration consistently across runs. The tool does not verify those experimental conditions for you.

## OpenMC handoff

Before any physical run, follow [the gated OpenMC handoff checklist](../reports/openmc_handoff_checklist.md). It requires a defensible benchmark, geometry/material mapping, nuclear-data provenance, a validated baseline, and recorded run metadata before candidate-level physical claims are made.
