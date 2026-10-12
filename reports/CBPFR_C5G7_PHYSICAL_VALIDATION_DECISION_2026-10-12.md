# CB-PFR C5G7 physical-validation decision — 2026-10-12

## Executive decision

**Status: NOT VALIDATED against the published C5G7 benchmark.** This is a completed evidence-based decision from the artifacts currently available, not a claim that no useful evidence exists. The available runs support internal execution/integrity checks and a descriptive numerical comparison. They do not support an external physical-validation pass because the archived CB-PFR model is a custom 2×2 fuel-assembly arrangement with a surrounding reflector, whereas the published standard 2-D C5G7 benchmark is a 16-assembly mini-core (eight UO₂ and eight MOX assemblies) with its own specified geometry and boundary conditions. Similar numerical k-effective values do not make geometrically different problems equivalent.

Primary benchmark source: Song et al., *GPU Based Two-Level CMFD Accelerating Two-Dimensional MOC Neutron Transport Calculation*, Table 1 reports C5G7 reference k-effective 1.18655 ± 9.5 pcm, maximum pin power 2.498 ± 0.16%, minimum pin power 0.232 ± 0.58%, and normalized assembly power results. The OECD/NEA C5G7-TD overview describes the underlying mini-core as sixteen assemblies: eight UO₂ and eight MOX, surrounded by a water reflector. Links: https://www.frontiersin.org/journals/energy-research/articles/10.3389/fenrg.2020.00124/full and https://oecd-nea.org/science/wprs/egrts/c5g7-td/.

## Evidence inventory reviewed

1. Screening campaign, GitHub Actions run [38182056526](https://github.com/thenextw4ng/cb-pfr/actions/runs/38182056526): 18 completed OpenMC runs, six custom layouts × three seeds. Recorded settings are 5,000 total batches, 500 inactive batches, 5,000 particles per batch (22.5 million nominal active histories per run). Artifact/export integrity checks pass, but its own metadata calls these smoke-test settings.
2. Canonical UMMU campaign, GitHub Actions run [38196703024](https://github.com/thenextw4ng/cb-pfr/actions/runs/38196703024): three independent seeds, each 7,000 batches, 500 inactive, 10,000 particles per batch (65 million nominal active histories per run). This is higher-budget than the 18-run screen, but it covers only the custom UMMU 2×2 arrangement.
3. The raw high-budget `assembly_fission.json` explicitly defines its reported metric as `max(assembly-integrated fission rate) / mean(assembly-integrated fission rate)` and says uncertainty is not propagated for correlated mesh bins. It calls the metric a dimensionless fission-rate proxy, not absolute power or a reactor-safety metric.

## k-effective arithmetic (descriptive only)

| Seed | OpenMC k-effective | Reported within-run standard deviation |
|---:|---:|---:|
| 720000 | 1.1863182340 | 9.4186 pcm |
| 730000 | 1.1865450004 | 9.6983 pcm |
| 740000 | 1.1866164010 | 9.6174 pcm |
| **Mean** | **1.1864932118** | — |
| Between-seed sample SD | — | **15.5684 pcm** |
| Standard error of the three-run mean | — | **8.9884 pcm** |

Against the published number 1.18655, the arithmetic difference is −5.6788 pcm. If the published ±9.5 pcm is treated as a one-standard-deviation uncertainty, combining it with the observed standard error gives approximately 13.08 pcm; the numerical difference is smaller than this combined uncertainty. **This is not a valid benchmark pass**, because the compared geometries / model definitions have not been shown to be identical. It is only a numerical proximity check and must not be described as validation.

## Why pin/assembly-power validation is not passed

The published reference gives standard C5G7 pin-power and assembly-power observables for the specified benchmark geometry. The archived CB-PFR output is a four-assembly, custom-layout tally and its peak-to-mean metric is a fission-rate proxy. No evidence in the current package establishes a one-to-one mapping between those four custom assembly tallies and the published standard C5G7 assembly/pin-power data. Therefore a numerical error, RMS error, or uncertainty-weighted pass/fail statistic for power cannot honestly be calculated from these non-equivalent observables.

## Gate-by-gate decision

| Gate | Decision | Evidence / reason |
|---|---|---|
| Run/artifact integrity for the 18-run screen | PASS | 18 records, unique seeds/statepoint hashes, common group structure/MGXS audit reported; screening only. |
| Six-layout/five-reflector-position invariant in archived screening inputs | PASS for the archived generated inputs | Raw-input audit found six distinct fuel patterns repeated three times and the five reflector positions unchanged. This is a structural check, not physical validation. |
| Higher-budget raw-statepoint availability for canonical UMMU | PASS | Three seed-specific statepoints and raw HDF5 audits are archived. |
| k-effective numerical proximity to published C5G7 value | DESCRIPTIVE CHECK ONLY | −5.68 pcm, but the custom 2×2 model is not demonstrated to be the standard 16-assembly benchmark geometry. |
| Source/eigenvalue convergence acceptance | NOT ESTABLISHED | The 18-run traces have material quarter-to-quarter shifts; the three-run UMMU campaign does not establish a predeclared convergence criterion for all layouts. |
| Pin/assembly-power comparison | NOT EVALUABLE from current evidence | Observable and geometry mapping to published reference has not been established. |
| External physical validation of all six CB-PFR layouts | FAIL / NOT DEMONSTRATED | No apples-to-apples benchmark case plus comparable power observable is present for all six layouts. |

## What can safely be concluded now

- The archived OpenMC runs executed and produced traceable output.
- The fixed-reflector and six-layout invariant is supported for the archived screening inputs.
- The higher-budget UMMU result is numerically close to the commonly reported C5G7 reference k-effective, but that coincidence cannot validate a custom 2×2 model against the standard 16-assembly benchmark.
- The current artifacts do **not** establish physical validity of the custom model, a validated ranking of all six layouts, reactor safety, or suitability for a real operating reactor.

## Minimum path to a genuine benchmark pass

Freeze a separate benchmark-validation case that exactly implements the published C5G7 geometry/materials/boundary conditions and tally definitions. Run it with independent seeds and a predeclared convergence rule; compare k-effective, maximum/minimum pin power, and normalized pin-power distribution against the published reference with uncertainties and consistent normalization. Only after that case passes should the six custom CB-PFR layouts be described as evaluated by a benchmark-checked transport model. The six layouts are a separate design study and must not be conflated with the benchmark reference case.
