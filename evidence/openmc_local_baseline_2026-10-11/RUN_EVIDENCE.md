# C5G7/OpenMC baseline: recorded execution evidence

**Recorded date:** 2026-10-11  
**Status:** raw evidence ZIP `OpenMC_HDF5_Evidence_2026-10-11.zip` is committed on `main`. GitHub Actions extracted the production statepoint and read it with the OpenMC 0.16.0 Python API; the API-derived `k_eff` mean and standard deviation matched the transcribed summary. See `reports/openmc_statepoint_audit_2026-10-11.md` and [the successful audit workflow](https://github.com/thenextw4ng/cb-pfr/actions/runs/38083671809).

## Reported result

`k_eff = 1.186394144702191 ± 0.000056113408647969484`

Reported run settings:
- OpenMC 0.16.0
- Eigenvalue mode
- Multi-group energy mode
- 20,000 batches; 500 inactive
- 10,000 particles per batch
- 19,500 active realizations
- 51 × 51 × 1 mesh tally (2,601 bins)
- Scores: flux, fission, nu-fission
- Statepoint: `c5g7-run/2d/statepoint.20000.h5`
- MGXS SHA-256: `170cc799f496e952465583bb078b2a88eae0f09886a821fd7ee8999d1eb93216`

The reported statepoint also contained `summary.h5`, one mesh tally with results shape `(2601, 3, 2)`, and a second tally with results shape `(1, 3, 2)`. These raw HDF5 shapes must not be interpreted as mean/std-dev without verifying OpenMC's data layout. Use the provided Python script and OpenMC API.

## Archived stage34 runs

Three archived directories were reported:
- `stage34_runs/run_01/`
- `stage34_runs/run_02/`
- `stage34_runs/run_03/`

Each reportedly contains `openmc.log`, `statepoint.100.h5`, and `summary.h5`. Their association with the six final candidate configurations has not been demonstrated by the supplied evidence.

## What this result supports

It supports the narrow statement that a C5G7/OpenMC eigenvalue run was reported as completed with the settings and scalar output above. It does **not** establish:
- that six optimization candidates were simulated and validated;
- that abstract QUBO categories map defensibly to C5G7 materials or depletion states;
- that CB-PFR has been physically validated;
- that flux/fission tallies represent absolute reactor power;
- that the model is benchmark-validated merely because the run completed;
- any reactor safety claim.

## Local verification

Activate the same environment used for OpenMC and run:

```bash
conda activate openmc-env
python scripts/audit_openmc_statepoint.py \
  --statepoint "$HOME/C5G7_openmc_production/c5g7_2d_20261011_001910/c5g7-run/2d/statepoint.20000.h5" \
  --outdir results/openmc_local_baseline_2026-10-11
```

Then inventory the run folders:

```bash
python scripts/inventory_openmc_runs.py \
  "$HOME/C5G7_openmc_production/c5g7_2d_20261011_001910" \
  --out results/openmc_local_baseline_2026-10-11/artifact_inventory.json
```

The resulting reports are machine-derived from local files; compare them with the transcribed evidence above before updating manuscript claims.
