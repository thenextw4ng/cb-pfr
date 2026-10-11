# Reproducibility

## Software and synthetic experiments

Install with `python -m pip install -e .`. Run unit tests with `python -m unittest discover -s tests -v`. The repository's CI workflow also compiles Python sources, runs the existing test suite and examples, audits archived evidence, and reproduces the frozen synthetic benchmark.

## OpenMC quick-check

See [OPENMC_EXECUTION.md](OPENMC_EXECUTION.md) and the pinned [quick-check workflow](../.github/workflows/c5g7-five-minute-quickcheck.yml). The recorded run used OpenMC 0.16.0, MIT-CRPG source commit `ba41bee54320ada0b4ac39a0dd2ca3c1d090a450`, seed base 811011, 20 total batches, 5 inactive batches, 100 particles per batch, and one thread. The uploaded artifact is linked from [Actions run 38112118549](https://github.com/thenextw4ng/cb-pfr/actions/runs/38112118549).

Use a fresh output directory; scripts intentionally refuse to overwrite prior results. Keep each run's configuration, commit SHA, seed, input SHA-256, statepoint SHA-256, OpenMC version, and raw audit together. A run is not reproducible from the scalar result alone.

## Independent seed aggregation

Run the assembly analysis once per distinct seed/statepoint, then:

```bash
python scripts/aggregate_c5g7_fission_replicates.py \
  --inputs results/seed-1/assembly_fission.json results/seed-2/assembly_fission.json results/seed-3/assembly_fission.json \
  --out results/replicate_aggregation.json
```

Each report must include a distinct integer `seed` and unique 64-character `statepoint_sha256`. The aggregator computes between-seed sample SD and standard error for the per-run peaking factor and assembly totals. It refuses a single run, duplicate seeds/hashes, missing provenance, mixed candidates, or invalid values.

## Reference comparison

```bash
python scripts/compare_c5g7_reference.py \
  --simulation-json results/seed-1/assembly_fission.json \
  --reference-csv examples/c5g7_published_reference_baseline.csv \
  --out results/new_benchmark_comparison.csv
```

This records a numerical (k_{eff}) screen and explicitly blocks the non-comparable power metric. The same command accepts the aggregate evidence JSON at `results/c5g7_repeatability_reexecution_2026-10-11.json`; use that as `--simulation-json` for the three-seed comparison. For aggregate data, the comparator uses between-seed sample SD divided by sqrt(n) as the standard error of the mean. Do not overwrite the committed comparison; use a new output path for each new run.


## Corrected-group repeatability re-execution

The [completed run 38112597526](https://github.com/thenextw4ng/cb-pfr/actions/runs/38112597526) ran 18 OpenMC cases (six layouts × three seeds), with 100 batches, 10 inactive, and 1,000 particles per batch. All group-structure and raw-HDF5 spatial mapping audits passed. Summary values and artifact provenance are in `results/c5g7_repeatability_reexecution_2026-10-11.json`. This is smoke-budget repeatability evidence, not benchmark acceptance.
