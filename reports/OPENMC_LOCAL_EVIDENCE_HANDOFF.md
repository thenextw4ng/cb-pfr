# OpenMC evidence handoff — 2026-10-11

This report links the existing CB-PFR repository evidence with a separately recorded local C5G7/OpenMC baseline. The repository's existing synthetic benchmark data and tests remain the authoritative evidence for the current CB-PFR software prototype.

## Existing repository evidence
The main branch already contains the CB-PFR implementation, tests/CI, the reduced synthetic benchmark runner and configuration, archival `results/per_seed_results.csv`, and methodological reproducibility/limitations audits. The recorded synthetic selected-feasibility rates are QUBO-only 0.857, point estimate 0.933, CB-PFR 0.976, and uniform margin 0.966. These are conditional synthetic results, not physical reactor results.

## Added local-run evidence
The `evidence/openmc_local_baseline_2026-10-11/` folder records the baseline scalar output and run configuration supplied from the user's local terminal. It is explicitly labelled as transcribed evidence because the HDF5 files themselves were not accessible to this GitHub integration.

## Added reproducibility tools
- `scripts/audit_openmc_statepoint.py`: read-only extraction of scalar statepoint metadata and tally mean/std-dev values through OpenMC's API.
- `scripts/inventory_openmc_runs.py`: artifact inventory and SHA-256 checksums.

## Still missing for a full candidate-level physical study
1. Actual HDF5 statepoint files or locally generated machine-derived exports.
2. Candidate IDs and exact configuration vectors matched to each run.
3. Verified proof that the five fixed reflector positions remain unchanged for each candidate.
4. Candidate-specific manifests, input hashes, logs, settings and statepoints.
5. A defensible QUBO-state-to-C5G7-material mapping and independent physical-validation protocol.

Do not claim that the six candidates have all been physically simulated until these are verified. This branch is a staging/evidence branch; it does not overwrite `main`.
