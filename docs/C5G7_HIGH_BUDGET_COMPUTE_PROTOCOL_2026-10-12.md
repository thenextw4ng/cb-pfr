# C5G7 higher-budget OpenMC batch protocol — 2026-10-12

## Purpose

Increase the amount of reproducible physical-simulation evidence available before downstream CB-PFR analysis. This is a project-level repeated layout study using the pinned MIT-CRPG C5G7 source, not an official benchmark reproduction for every noncanonical layout and not a reactor-safety analysis.

## Design and compute budget

- Six assembly-level arrangements, each with exactly two MOX and two UO2 assemblies; the five reflector positions remain fixed.
- Three independent seed rounds: 620000, 630000, and 640000. Candidate seed offsets are assigned deterministically by the study runner.
- Per run: 5,000 total batches, 500 inactive batches, 5,000 particles per batch, two OpenMC threads.
- Total runs: 18.
- Nominal histories across the full study: 450,000,000; nominal active histories after inactive batches: 405,000,000.
- OpenMC version: 0.16.0, Python 3.12, pinned through the conda-forge environment in GitHub Actions.
- Source commit: `ba41bee54320ada0b4ac39a0dd2ca3c1d090a450`.
- Corrected seven-group boundaries are audited as `[1e-5, 0.0635, 10, 100, 1000, 500000, 1000000, 20000000] eV`.

This is a higher-budget follow-up to the 100-batch / 1,000-particle smoke profile. It is intentionally not labelled benchmark-grade or converged in advance.

## Automated outputs

If all transport jobs and integrity checks succeed, the final GitHub Actions artifact `cbpfr-c5g7-high-budget-complete-2026-10-12` contains:

- the three complete study directories, including raw statepoints and case manifests;
- `run_level_results.csv`, produced only after re-hashing statepoints and MGXS, checking manifests/settings/source identity/group boundaries, and re-parsing the tally outputs;
- `export_audit.json`, which records evidence provenance and integrity status;
- `objective_audit.json`, with descriptive per-layout estimates and Student-t intervals for the repeated-run metrics;
- `budget_comparison.json`, comparing the higher-budget estimates against the archived smoke runs.

Raw outputs and reports are retained as GitHub Actions artifacts for 90 days. The small run-level CSV and JSON reports should be copied into the research archive after the run succeeds; the raw statepoints should be downloaded and preserved separately for long-term reproducibility.

## Fail-closed decision policy

This workflow does not set a candidate-specific acceptable (k_\mathrm{eff}) band, infer one from the observed data, or select a physical winner. The post-run audit must report no winner. A downstream selector QUBO is only appropriate after the project has predeclared and justified physical acceptance criteria and independently reviewed the tally mapping.

A successful workflow proves that the specified jobs ran and the declared data-integrity checks passed. It does not, by itself, prove convergence, reproduce the official benchmark, establish physical superiority, validate absolute power, certify reactor safety, or demonstrate quantum advantage. If any run, source/hash audit, or output parsing fails, the batch is incomplete and must not be promoted as a complete 18-run study.
