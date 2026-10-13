# Integrated C5G7, OpenMC, CB-PFR, and selector-QUBO workflow

Status: software integration workflow. Physical validation is not certified.

## What the integrated command does

The command `scripts/run_c5g7_cbpfr_pipeline.py` joins a completed run-level OpenMC CSV to the CB-PFR conservative screen and post-physics selector-QUBO solver.

It validates the six declared 2x2 UO2/MOX layouts; checks the corrected seven-group energy-boundary audit, hashes, common MGXS, run settings, unique seeds and unique statepoints; aggregates k-effective and fission-rate-peaking observations while keeping within-run uncertainty distinct from between-seed variability; applies caller-declared limits; emits no winner if no candidate passes; constructs the six-variable one-hot selector QUBO only after the physics screen; compares solver output with exact enumeration; and writes one JSON evidence bundle with provenance, decision status, solver metadata, nonclaims, and a bundle hash.

## Run

The CSV must come from completed corrected-group OpenMC runs and contain all columns enforced by `scripts/run_c5g7_cbpfr_physical_selection.py`, including candidate ID, layout signature, seed, k-effective mean and standard deviation, fission-rate peaking factor, statepoint and MGXS SHA-256, group-structure audit and boundaries, and compute settings.

Replace each uppercase token below with a value from a documented and approved study protocol:

```bash
python scripts/run_c5g7_cbpfr_pipeline.py \
  --run-level-csv results/STUDY/run_level_results.csv \
  --out results/STUDY/cbpfr_integrated_bundle.json \
  --backend exact \
  --keff-min APPROVED_KEFF_LOWER_BOUND \
  --keff-max APPROVED_KEFF_UPPER_BOUND \
  --fission-peaking-max APPROVED_PEAKING_LIMIT \
  --uncertainty-multiplier PREDECLARED_MULTIPLIER \
  --keff-scale APPROVED_KEFF_SCALE \
  --fission-peaking-scale APPROVED_PEAKING_SCALE \
  --risk-weight PREDECLARED_RISK_WEIGHT \
  --min-batches MINIMUM_BATCHES \
  --min-particles MINIMUM_PARTICLES \
  --min-replicates 3
```

Limits are deliberately not presented as universal defaults. They need a documented scientific rationale before final candidate comparisons. The command refuses to overwrite an existing output.

For a classical stochastic sampler, install the optional Ocean dependencies and use `--backend ocean-sa`. For actual hardware use `--backend dwave-qpu` with an independently configured provider token and available QPU. Retain provider run metadata. Ocean simulated annealing is classical, not quantum hardware.

## Keep the two QUBOs separate

- **Material-placement QUBO:** four binary variables; its penalty enforces exactly two MOX positions. The six feasible layouts tie, so this formulation does not encode k-effective or an OpenMC tally.
- **Post-physics selector QUBO:** six one-hot variables, one per layout, constructed from repeated OpenMC evidence and the declared CB-PFR screen. This is the QUBO solved by the integrated command.

The command ingests completed OpenMC outputs; it does not launch OpenMC transport itself. Run preparation and execution remain the responsibility of `scripts/run_c5g7_layout_study.py` or the separately configured repeated-run workflow.

## Status interpretation

- `PIPELINE_COMPLETE_SELECTION_REPRODUCED`: the declared screen emitted an accepted candidate and the configured solver's returned selection agrees with the exact reference. With the exact backend, this only verifies the small selector solve.
- `PHYSICS_SCREEN_COMPLETED_SOLVER_SELECTION_NOT_ACCEPTED`: a conservative-screen candidate exists, but the stochastic solver's best returned sample failed exact-reference, one-hot, or screening checks.
- `BLOCKED_NO_CONSERVATIVELY_FEASIBLE_CANDIDATE`: no candidate passes the caller-declared screen; no solver selection is accepted.

Every status is software/data-path evidence, not official C5G7 benchmark acceptance, a convergence certificate, physical superiority, a reactor-safety conclusion, or quantum advantage. Fission-rate peaking is a dimensionless relative proxy, not absolute power.


## Export repeated study outputs into the pipeline

For new OpenMC runs, first execute the existing C5G7 study runner in `run` mode for each independent seed round, using the same batches/inactive/particles/threads and a different seed base. Then export and audit the raw statepoints into the run-level CSV:

```bash
python scripts/export_c5g7_run_level_evidence.py \
  --study-summary results/round1/STUDY_SUMMARY.json results/round2/STUDY_SUMMARY.json results/round3/STUDY_SUMMARY.json \
  --out-csv results/repeated-study/run_level_results.csv \
  --audit-out results/repeated-study/export_audit.json
```

The exporter re-hashes statepoints and MGXS files, checks the run manifests and corrected group boundaries, re-parses the mesh tally through the OpenMC API, and verifies that the parsed k-effective mean/SD match the study summary. It rejects partial studies, duplicate seeds/statepoints, mismatched budgets, inconsistent MGXS hashes, or nonstandard group structures. It requires at least three complete six-layout study summaries and does not launch OpenMC itself.

Then pass the exported CSV to the integrated pipeline command above. Archived smoke rows may instead use `scripts/prepare_c5g7_selection_input.py`, but that adapter explicitly restores only the documented smoke settings; it does not upgrade those historical runs to benchmark-grade evidence.
