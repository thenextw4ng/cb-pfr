# Normalized MGXS repeatability smoke study

Workflow: https://github.com/thenextw4ng/cb-pfr/actions/runs/38100905238
Artifact with raw statepoints and per-run files: https://github.com/thenextw4ng/cb-pfr/actions/runs/38100905238/artifacts/11687737079
Pinned upstream commit: `ba41bee54320ada0b4ac39a0dd2ca3c1d090a450`.

This is a fresh rerun after normalizing the first and last energy-group boundaries in the copied upstream `materials.py` before MGXS generation. All 18 runs use the same production-identical MGXS SHA-256 `170cc799f496e952465583bb078b2a88eae0f09886a821fd7ee8999d1eb93216`. The previous workflow's one-ULP root-boundary discrepancy is no longer present in this run.

- 3 rounds × 6 layouts = 18 runs.
- 18 unique seeds and 18 unique statepoint hashes.
- All raw HDF5 audits pass.
- Common settings: 100 batches, 10 inactive, 1,000 particles/batch, one thread.
- Rank correlations between rounds: 0.886, 0.943, 0.943.

The MGXS reproducibility issue is fixed for this rerun, but the physics runs remain low-budget smoke tests. Three seeds per layout are not enough to calibrate uncertainty, and ranking by (k_\mathrm{eff}) is descriptive only.
