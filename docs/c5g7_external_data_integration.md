# External C5G7 data bridge: QUBO + OpenMC evidence + CB-PFR

## Why this is a separate formulation

The existing Usmanov-style QUBO encodes `fresh / once_burned / twice_burned` categories. The C5G7 2x2 placement study encodes UO2/MOX assembly positions. They are not interchangeable. This bridge therefore creates an explicitly separate **C5G7 layout-selector QUBO** from source-attributed, layout-matched result data; it does not silently translate the legacy QUBO.

## Public model/source

The upstream [MIT-CRPG reactor-physics benchmark repository](https://github.com/mit-crpg/benchmarks) includes an OpenMC C5G7 model. The OECD/NEA [C5G7 benchmark page](https://www.oecd-nea.org/jcms/pl_13548/benchmark-on-deterministic-transport-calculations-without-spatial-homogenisation) and its cited specification define the benchmark. These sources provide a model/specification; they do **not** automatically provide comparable result rows for all six non-reference material permutations.

The repository includes one source-attributed published baseline row in `examples/c5g7_published_reference_baseline.csv`, taken from Song et al. (2020), [*GPU Based Two-Level CMFD Accelerating Two-Dimensional MOC Neutron Transport Calculation*](https://doi.org/10.3389/fenrg.2020.00124). The paper reports the canonical C5G7-2D reference (k_{eff}=1.18655\pm9.5\) pcm and maximum pin power 2.498 with a reported relative uncertainty of 0.16%. The (k_{eff}) uncertainty is stored as 0.000095; the max-pin-power relative uncertainty is converted to an absolute uncertainty in the optional peaking-factor field. Treat this as **one canonical baseline only**, not six candidate results, not a run of the user's OpenMC model, and not a result for the other five permutations.

## Input CSV contract

Start from `examples/c5g7_external_results_template.csv` or inspect the one-row published baseline in `examples/c5g7_published_reference_baseline.csv`. Required columns:

- `candidate_id`: one of the six IDs `c5g7-2x2-<signature>`, where signature order is p00,p01,p10,p11 and M=MOX/U=UO2.
- `benchmark_case`: exact benchmark/model case and boundary-condition description.
- `source_url`: URL to the source publication/repository/data artifact.
- `source_kind`: e.g. `published_reference`, `upstream_model_run`, or `local_openmc_run`.
- `keff_mean`, `keff_uncertainty`, `keff_uncertainty_kind`: keep statistical uncertainty distinct from benchmark/model bias.
- Optional `fission_rate_peaking_factor`, `fission_rate_peaking_uncertainty`, `configuration_hash`, `notes`.

Only one documented aggregate row per candidate is accepted. Do not copy the canonical reference value into other layouts. A missing layout stays missing.

## CLI

```bash
python scripts/run_c5g7_external_data_bridge.py --input examples/c5g7_external_results.csv --output results/c5g7_external_bridge.json
```

For a complete six-layout dataset, explicitly choose an objective:

```bash
python scripts/run_c5g7_external_data_bridge.py --input examples/c5g7_external_results.csv --output results/c5g7_external_bridge.json --objective-column fission_rate_peaking_factor --direction min
```

The second command requires real peaking-factor values for all six candidates. The script refuses to invent values or rank incomplete coverage. `keff` is not automatically minimized or treated as a safety objective; the user must choose the objective and predeclare physical acceptance limits separately.

## What this integration does and does not claim

- Loads source-attributed, candidate-matched C5G7 data.
- Reports missing candidates rather than imputing them.
- Builds a data-derived one-hot QUBO over six layout IDs only when all six have the chosen observed metric.
- Can apply CB-PFR-style uncertainty-expanded limits only when explicit metric limits are supplied by the researcher.
- Does not run OpenMC, infer missing layout results, establish benchmark validity, or validate the legacy Usmanov QUBO.
- Published values are only comparable when benchmark variant, geometry, materials, cross sections, tallies, normalization, and uncertainty definition match.
