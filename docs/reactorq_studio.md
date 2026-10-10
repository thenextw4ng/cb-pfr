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


## Phase 2: auditable optimizer-run records

For each optimizer invocation, preserve the raw output and create a run record containing at least:

- unique `run_id`, optimizer name/version, seed (or `null` if unseeded), full parameter object, stopping condition, and run status;
- one `candidate_records` entry per recorded candidate, with a stable candidate ID, the full binary `candidate_vector`, rank, QUBO energy, and independently recorded feasibility flag. The validator rejects duplicate IDs, duplicate vectors, duplicate ranks, non-binary vectors, and non-finite values;
- `objective_value` when a separate objective is available; do not assume QUBO energy is interchangeable with a physical objective;
- `failure_reason` for failed, cancelled, or timed-out runs;
- `evidence_kind` and `physical_simulation_performed` provenance fields.

Validate a raw experiment log before analyzing it:

```bash
python scripts/validate_optimizer_runs.py --input results/optimizer_runs.json --output results/optimizer_runs.validated.json
```

Summarize the validated experiment, including completed/failed run counts, candidate feasibility rate, best recorded objective values, and ranking stability across completed runs:

```bash
python scripts/analyze_optimizer_experiment.py --input results/optimizer_runs.validated.json --output results/optimizer_experiment_summary.json --top-k 3 --objective-sense min
```

Use `--objective-sense max` when higher objective values are better. Objective summaries are only comparable within a documented experiment and objective definition. Candidate feasibility rate is the fraction of recorded candidate rows marked feasible, not the probability that a future optimizer run succeeds. Failed/interrupted runs remain in the run denominator for reliability counts but are excluded from ranking-stability calculations. The tools validate record structure, not whether the records genuinely came from the stated optimizer. Keep raw logs immutable and record software/configuration hashes externally when available. A complete synthetic input template is provided at `examples/optimizer_runs.example.json`; it is clearly labelled as a template, not research data.
