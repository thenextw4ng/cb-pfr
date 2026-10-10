# Phase 5–10 — Transport integration, evidence gates, repeatability, and release protocol

## Purpose and honest status

This phase adds the executable handoff from the six-layout reformulation to the public MIT CRPG C5G7 OpenMC source model. The adapter copies the audited upstream model into isolated candidate directories, changes only the exact 3×3 core-lattice assignment and explicit run settings, builds model XML, optionally runs OpenMC, and records hashes, logs, statepoint path, eigenvalue estimate/uncertainty, and raw available tallies.

**Repository-side implementation is prepared; physical evidence is not yet complete.** This environment has not run OpenMC, has not generated a statepoint, and has not verified the canonical case against the OECD/NEA reference. The default profile is deliberately a small smoke test (100 batches, 10 inactive, 1,000 particles) and is not benchmark-grade. Passing software CI cannot replace a physical run.

## Stage 5 — Build the model adapter

1. Stage the public upstream repository and record its full Git SHA:

       mkdir -p external
       python scripts/prepare_c5g7_reference.py --destination external/mit-crpg-benchmarks

2. Generate the six-layout design space:

       mkdir -p results
       python scripts/enumerate_c5g7_layouts.py --output results/c5g7_design_space.json

3. Prepare isolated input cases without requiring OpenMC:

       python scripts/run_c5g7_layout_study.py \
         --source-root external/mit-crpg-benchmarks \
         --design-space results/c5g7_design_space.json \
         --output results/c5g7-layout-study-prepared \
         --mode prepare

The adapter verifies the source provenance record, exact design-study identifier, all six unique layouts, two/two material counts, one canonical layout, and exact source-template lines before patching. It refuses to overwrite the study output. Each case contains a source copy, explicit layout, input hashes, and a manifest. The patch is limited to the core assembly lattice and the three explicit run settings.

## Stage 6 — Run and verify the canonical baseline first

Install a working OpenMC build that supports the source's multi-group APIs and verify the OpenMC executable is on PATH. Then run a smoke test:

       python scripts/run_c5g7_layout_study.py \
         --source-root external/mit-crpg-benchmarks \
         --design-space results/c5g7_design_space.json \
         --output results/c5g7-layout-study-smoke \
         --mode run --batches 100 --inactive 10 --particles 1000 --threads 1

The canonical source arrangement is processed first. Review STUDY_SUMMARY.json, per-case CASE_RESULT.json, build/OpenMC logs, XML hashes, and statepoint. A smoke-test eigenvalue is only a software/runtime diagnostic. For benchmark verification, use benchmark-prescribed tallies, model variant, convergence protocol, and sufficiently converged settings, then compare to the correct primary reference quantities with statistical and methodological uncertainty. Do not set a passing numerical tolerance by looking at the observed result.

The adapter stops after a failed or unparsed case. The raw statepoint and logs are retained. A run that exits zero but whose statepoint cannot be parsed is not treated as validated.

## Stage 7 — Evaluate the six layouts

Only after the canonical baseline's model and tallies have passed independent review, repeat with a separate fresh output directory and predeclared production settings. Every candidate must use the same source revision, nuclear data, settings, tallies, and convergence rules. Do not compare a low-statistics smoke run to a converged reference or rank candidates by raw tally values that are not normalized comparably.

The upstream model includes a mesh tally (tally 1, scores flux/fission/nu-fission) and a global tally (tally 2). These should be reviewed for physical meaning and normalization before deriving assembly/pin power metrics. The adapter stores raw means and standard deviations rather than silently inventing power conversion or a winner.

## Stage 8 — Repeated-run analysis

The existing experiment log and repeated-run analysis tools can analyze optimizer records; they do not independently create physical replicas. For physical uncertainty, define independent seeds/replicates and convergence criteria in advance, retain every run's settings and outputs, and distinguish:
- Monte Carlo sampling uncertainty within a run;
- between-seed variation;
- differences among candidate layouts;
- uncertainty due to nuclear data/model form, which is not estimated by seed repetition alone.

Do not count correlated batches from one run as independent full-run replicates. Aggregate candidate ranking only after verifying tally semantics, units, normalization, and uncertainty propagation. A production-grade replicate orchestrator and predeclared statistical analysis should be added only after the smoke run confirms the installed OpenMC API and output schema.

## Stage 9 — CB-PFR evaluation

CB-PFR is a post-optimization ranking layer, not the transport solver. Its physical-evaluation input must be traceable to verified candidate outputs and include metric definitions, units, uncertainty provenance, acceptance limits, and a source hash. Compare CB-PFR to predeclared baselines (for example point-estimate ranking and a uniform-margin baseline) under the same held-out or replicate protocol. Report failures and missing values; do not impute failed transport runs as physically feasible. Synthetic calibration rates remain separate from all physical results.

## Stage 10 — Final audit and publication gate

- [ ] Pin and archive the upstream full Git commit and all relevant input hashes.
- [ ] Review source license/attribution and cite the OECD/NEA primary specification.
- [ ] Reproduce the canonical case using benchmark-compatible settings.
- [ ] Document agreement/disagreement with reference values and the uncertainty budget.
- [ ] Predeclare physical metrics, limits, candidate selection, and repeat protocol.
- [ ] Run all six candidates with comparable settings and complete provenance.
- [ ] Perform repeated-run and baseline-comparison analyses on actual physical records.
- [ ] Ensure every paper claim maps to a report, raw output, or test.
- [ ] Keep the legacy abstract burnup-state QUBO separate; no defensible mapping to C5G7 has been established.

## Important boundary

The code now automates input preparation and can invoke a real transport run when the user environment has OpenMC. It does not install nuclear transport software in the GitHub connector, provision a suitable runtime, or create valid physical data in the absence of a run. Therefore, stage 5's adapter work is implemented, while stages 6–10 remain conditional on real execution, baseline review, and generated data. No numerical physical results are claimed by this report.
