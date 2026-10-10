# OpenMC statepoint semantic cross-check

## Purpose

This protocol cross-checks a machine-derived statepoint_audit.json against the
recorded result_summary.json. It compares the scalar eigenvalue estimate and
uncertainty, run settings, realization count, and expected mesh tally.

## Local execution

```bash
conda activate openmc-env
python scripts/audit_openmc_statepoint.py \
  --statepoint "$HOME/C5G7_openmc_production/c5g7_2d_20261011_001910/c5g7-run/2d/statepoint.20000.h5" \
  --outdir results/openmc_local_baseline_2026-10-11
python scripts/compare_openmc_baseline.py \
  --audit results/openmc_local_baseline_2026-10-11/statepoint_audit.json \
  --baseline evidence/openmc_local_baseline_2026-10-11/result_summary.json \
  --out results/openmc_local_baseline_2026-10-11/baseline_comparison.json
```

The comparison script exits 0 only if every required check passes and 2 on
mismatch or missing evidence. It refuses to overwrite its output.

## What PASS means

PASS means the OpenMC API-derived export agrees with the currently recorded
summary for the checks implemented. It is a consistency check, not an independent
benchmark validation: the summary was transcribed from terminal output, so the
provenance is shared until an independent reference comparison is performed.

## What PASS does not mean

- It does not verify that the C5G7 model matches the official benchmark specification.
- It does not map the abstract QUBO categories to C5G7 UO2/MOX/depletion states.
- It does not establish which of the six layouts was simulated.
- It does not prove power normalization, physical limits, or reactor safety.
- It does not substitute for a common-budget comparison with replicated candidate runs.

## Failure handling

Do not edit the expected summary to make a mismatch disappear. Preserve the audit,
comparison report, input XMLs, logs, statepoint hash, and software/data provenance;
then investigate whether the difference is a transcription error, an API/version
difference, a different run, or a substantive model discrepancy.
