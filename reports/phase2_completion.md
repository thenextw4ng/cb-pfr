# Phase 2 Completion Report — Optimizer Experiment Provenance

**Status:** implemented and merged into `integration/reactorq-studio`  
**Integration commit:** `dedbf6030dbfb2a8ce0f8bbc553ec43978b8d873` (squash merge of PR #11)  
**Pull request:** https://github.com/thenextw4ng/cb-pfr/pull/11  
**Pre-merge verification:** GitHub Actions run https://github.com/thenextw4ng/cb-pfr/actions/runs/38034844754 passed on Python 3.10, 3.11, and 3.12.

## Completed checklist

- [x] Each run records a unique ID, optimizer and version, seed (or null), full parameter object, stopping condition, and run status.
- [x] Failed, cancelled, and timed-out runs remain in the dataset and require a failure reason.
- [x] Candidate records contain stable IDs, full binary candidate vectors, rank, QUBO energy, feasibility, and optional separate objective values.
- [x] Validation rejects non-finite values, malformed vectors, duplicate IDs/ranks/vectors, and candidate ID/vector drift across runs.
- [x] Experiment-wide candidate-vector dimensional consistency is checked.
- [x] Summary separates completed runs from failed/interrupted runs, computes candidate-row feasibility rate, reports best observed objective and best feasible objective, and analyzes top-k ranking stability across completed runs.
- [x] Objective minimization and maximization are supported explicitly; objective values are never inferred from QUBO energy.
- [x] Validation and analysis CLIs produce strict JSON and refuse to overwrite an existing output file.
- [x] A synthetic-only example record, documentation, and automated unit/end-to-end CLI tests are included.
- [x] CI passes across Python 3.10, 3.11, and 3.12.

## Main artifacts

- `src/cbpfr/experiment_log.py` — schema validation and stable candidate identity.
- `src/cbpfr/experiment_analysis.py` — quality, feasibility, failure, and repeatability summaries.
- `scripts/validate_optimizer_runs.py` — validates recorded run logs.
- `scripts/analyze_optimizer_experiment.py` — generates experiment summary JSON.
- `examples/optimizer_runs.example.json` — clearly labelled synthetic template.
- `tests/test_experiment_log.py`, `tests/test_experiment_analysis.py`, `tests/test_experiment_cli.py` — regression and CLI tests.
- `docs/reactorq_studio.md` — schema, commands, and interpretation guidance.

## Scientific limitations

This phase does not run an optimizer or prove that a log came from the claimed solver; users must preserve original raw outputs and record the true software/configuration provenance. The feasibility rate is the fraction of candidate rows marked feasible, not the probability of future run success. Ranking stability is descriptive, not a global-optimality certificate. No physical OpenMC validation or reactor metric is produced by this phase.

## Reproduction commands

```bash
python scripts/validate_optimizer_runs.py --input results/optimizer_runs.json --output results/optimizer_runs.validated.json
python scripts/analyze_optimizer_experiment.py --input results/optimizer_runs.validated.json --output results/optimizer_experiment_summary.json --top-k 3 --objective-sense min
```
