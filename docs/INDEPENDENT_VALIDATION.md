# Independent benchmark comparison and validation status

## Reference selected

Song et al. (2020), *GPU Based Two-Level CMFD Accelerating Two-Dimensional MOC Neutron Transport Calculation*, Frontiers in Energy Research, Table 1: https://doi.org/10.3389/fenrg.2020.00124. The article reports a canonical 2-D C5G7 reference (k_{eff}=1.18655pm9.5) pcm, i.e. standard uncertainty (0.000095), and maximum normalized pin power (2.498pm0.16\%). The article describes a seven-group, 51x51-pin problem. The OECD/NEA primary specification remains the controlling source for full model-identity review.

This is a published computational benchmark reference, not a direct experiment on a physical reactor. It can support code-to-reference verification only when the model, observable, normalization, and statistical interpretation match.

## Numerical (k_{eff}) screen from the five-minute run

The quick-check produced (k_{eff}=1.1728029349321403) with reported within-run standard deviation (0.019472323678449033). Against the published reference:

[
\Delta = k_{sim}-k_{ref}=-0.0137470650678597
]

[
\epsilon_{rel}=100\frac{k_{sim}-k_{ref}}{k_{ref}}\approx -1.1587\%.
]

If the two reported standard uncertainties are treated as independent, the combined standard uncertainty is approximately (0.01947256) and the difference is approximately (-0.706) combined standard uncertainties. This is **not** a meaningful acceptance result: the simulation uncertainty is very large, the run has only 15 active batches at 100 particles per batch, and full model-identity review remains blocked. It neither demonstrates agreement nor establishes a discrepancy in the underlying model.

The machine-readable comparison is recorded in `results/benchmark_comparison.csv`. The script `scripts/compare_c5g7_reference.py` labels this result `NUMERICAL_SCREEN_ONLY_MODEL_IDENTITY_BLOCKED_LOW_STAT`, rather than PASS.

## Why the power comparison is blocked

The legacy baseline CSV has a column called `fission_rate_peaking_factor` containing 2.498. The cited publication identifies 2.498 as *maximum normalized pin power*. The local code computes maximum assembly-integrated fission-rate tally divided by the mean over four assemblies. These are not the same observable, so no relative error is calculated. The historic CSV row is preserved; a metric-aware comparator emits a blocked row rather than silently treating the values as comparable.

The article also reports assembly-power quantities for a different grouping/normalization. Those cannot be substituted for the local four-assembly proxy without a verified assembly-index mapping and matching normalization.

## Current decision

- **Computational reference located:** YES.
- **Like-for-like (k_{eff}) numerical screen:** RECORDED, low-statistics only.
- **Benchmark reproduced:** NOT ESTABLISHED.
- **Pin/assembly power comparison:** BLOCKED pending matched observable and reference extraction.
- **Physical experimental validation:** NOT ESTABLISHED; no suitable physical experiment dataset has been identified for this specific configuration.
- **Acceptance criteria:** no official pass/fail threshold has been inferred from project-provisional screening limits.

Required next evidence: a high-budget corrected-group canonical run with independent seeds, primary-specification review/sign-off, documented source and nuclear-data provenance, convergence assessment, and a reference comparison of matched observables with appropriate uncertainty treatment.
