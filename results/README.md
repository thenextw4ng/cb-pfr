# Results and evidence

Results are immutable evidence snapshots. Write new runs to new paths; do not overwrite historical statepoints or comparison tables.

## Key artifacts

- `main_results.csv`, `per_seed_results.csv`: frozen synthetic CB-PFR experiment; synthetic-only evidence.
- `c5g7_repeatability_normalized_2026-10-11/`: prior low-budget multi-seed run records; see associated audit scripts and reports before using as benchmark evidence.
- `c5g7_corrected_group_repeatability_smoke_2026-10-11/`: corrected group-structure smoke data, not a converged validation run.
- `benchmark_comparison.csv`: (k_{eff}) numerical screen against the published C5G7 reference and an explicitly blocked assembly-power comparison. It is not an acceptance report.
- `c5g7_layout_smoke_2026-10-10/`: historical smoke outputs; preserve for provenance.

## Evidence classes

1. **Synthetic reproduction:** software reproducibility under the synthetic data-generating process.
2. **Transport execution:** OpenMC created a statepoint and the raw-HDF5 audit passed.
3. **Benchmark numerical comparison:** a metric-aware difference is recorded with uncertainty and model-identity caveats.
4. **Benchmark reproduction:** requires verified model identity, appropriate compute budget, convergence and comparable observables.
5. **Experimental physical validation:** requires suitable experimental measurements and uncertainty/provenance; not established by the current repository.


## Re-executed corrected-group study

The completed [18-run repeatability workflow](https://github.com/thenextw4ng/cb-pfr/actions/runs/38112597526) reran six layouts with three independent seeds each. All group-structure audits passed, statepoint hashes were unique, and the independent raw-HDF5 spatial-mapping audit passed all 18 cases. The compact summary is `c5g7_repeatability_reexecution_2026-10-11.json`; the complete run artifact is linked from the workflow page.
