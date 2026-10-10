# Recorded local OpenMC baseline evidence

This folder records the diagnostic information supplied from the user's local C5G7/OpenMC run on 2026-10-11. It is not a copy of the HDF5 statepoint itself.

## Files
- `run_manifest.json`: run configuration/provenance reported from the local machine.
- `result_summary.json`: reported scalar baseline result.
- `RUN_EVIDENCE.md`: detailed evidence boundary and interpretation.
- `../../scripts/audit_openmc_statepoint.py`: read-only local extraction script.
- `../../scripts/inventory_openmc_runs.py`: local artifact inventory/hash script.

## Important limitation
The local HDF5 files were not transferred to this GitHub integration during this commit. Therefore, the scalar values below are transcribed from terminal output supplied by the researcher, not independently re-read by this commit. Run the scripts locally to regenerate machine-derived reports and compare the results.

Do not treat the baseline as validation of CB-PFR or of any candidate configuration.
