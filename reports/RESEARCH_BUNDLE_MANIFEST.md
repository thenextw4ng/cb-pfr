# Research bundle manifest — OpenMC evidence handoff

**Branch:** `openmc-evidence-20261011`  
**Base:** `main`  
**Purpose:** stage the local C5G7/OpenMC execution evidence and reproducibility utilities without overwriting the current release branch.

## Contents already in the repository base
- CB-PFR source package and abstract QUBO implementation.
- Unit tests and GitHub Actions workflow.
- Frozen synthetic benchmark configuration and runner.
- Archived trial-level synthetic data: `results/per_seed_results.csv`.
- Existing reproducibility, limitations, and release-audit documents.
- Working-paper metadata and software citation metadata.

## Added in this branch
- `evidence/openmc_local_baseline_2026-10-11/run_manifest.json`
- `evidence/openmc_local_baseline_2026-10-11/result_summary.json`
- `evidence/openmc_local_baseline_2026-10-11/RUN_EVIDENCE.md`
- `evidence/openmc_local_baseline_2026-10-11/README.md`
- `scripts/audit_openmc_statepoint.py`
- `scripts/inventory_openmc_runs.py`
- `reports/OPENMC_LOCAL_EVIDENCE_HANDOFF.md`

## Download a ZIP of the branch
GitHub automatically provides a source archive for this branch:
https://github.com/thenextw4ng/cb-pfr/archive/refs/heads/openmc-evidence-20261011.zip

The ZIP contains the tracked repository files on this branch. It does **not** contain the user's untransferred local HDF5 statepoint files.

## Verification status
- GitHub accepted the seven added files on this branch.
- Existing repository documentation records a prior independent computational rerun of the synthetic benchmark, with substantive row-level outputs and aggregate rates matching the archive. This is not external third-party replication.
- The newly added OpenMC audit/inventory scripts have not been executed against the user's local HDF5 directory by this GitHub integration. Run them locally in the `openmc-env` environment before treating their generated outputs as verified.
- No test pass/fail claim is made for the new scripts in this commit.
- The recorded `k_eff` and run settings are transcribed from the terminal output supplied by the researcher; they are not independently recomputed by this commit.

## Data that still must be transferred from the Mac
The following are not included because this session could not read the local filesystem:
- `statepoint.20000.h5` and `summary.h5`
- archived stage34 statepoints, summaries, and logs
- actual candidate configuration vectors and manifests, if they exist
- locally generated tally CSVs/plots after the audit script is run

Do not commit large raw statepoints to Git without checking repository limits and data provenance. Prefer a compact, hash-verified evidence export, and store large files in an appropriate research archive if necessary.
