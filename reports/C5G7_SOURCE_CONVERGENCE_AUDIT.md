# OpenMC source-convergence diagnostic

The upstream builder attempted to set entropy-mesh attributes that OpenMC 0.16.0 ignores. The corrected runner replaces those lines with a real `openmc.RegularMesh` assigned to `settings.entropy_mesh`, using 51×51×1 bins. The corrected statepoint should then contain both batch-wise (k)-generation estimates and source entropy. The audit tool `scripts/audit_c5g7_source_convergence.py` exports those traces and summarizes first/last quarter means, half-window differences, and descriptive OLS slopes. It now reports the inactive pre-tally interval separately from active batches; this matters because active-only traces cannot show whether the fission source stabilized before tallies began.

Run it in an environment with OpenMC installed:

```bash
python scripts/audit_c5g7_source_convergence.py \
  --statepoint /path/to/statepoint.7000.h5 \
  --out-json analysis/source_convergence.json \
  --out-csv analysis/source_convergence.csv
```

The tool intentionally returns `DIAGNOSTIC_REVIEW_REQUIRED`, not a convergence pass. It records descriptive inactive-interval entropy and k-generation summaries separately, plus active-interval traces. There is no universal C5G7 entropy-slope cutoff that can be applied without justification. Inspect the complete inactive and active traces, predeclare any project threshold before assessing a campaign, and increase inactive batches or histories if source stability is unresolved. A converged source is necessary but not sufficient for benchmark acceptance.

OpenMC documentation: [statepoint file format](https://docs.openmc.org/en/latest/io_formats/statepoint.html) and [Shannon entropy settings](https://docs.openmc.org/en/stable/usersguide/settings.html).
