# Fixed-budget R&S and classical SQA comparison — 2026-10-11

**Workflow:** https://github.com/thenextw4ng/cb-pfr/actions/runs/38121832440  
**Workflow result:** success  
**Artifact:** c5g7-fixed-budget-rs-sqa (machine-readable `comparison.json`)  
**Status:** RETROSPECTIVE_SMOKE_DATA_COMPARISON_NOT_PHYSICAL_VALIDATION

## Question

Does the existing CB-PFR heuristic select a different or demonstrably better C5G7 layout than a fixed-budget ranking-and-selection (R&S) baseline when both use the same archived OpenMC evidence?

## Input and reproducibility checks

- 18 archived corrected-group OpenMC rows: six 2×2 UO₂/MOX layouts × three independent seeds per layout.
- All group-structure audits passed; statepoint hashes and seed IDs are unique.
- All rows share MGXS SHA-256 `a4328a7b012321fbe8e661745aa135f0a2eecd34cf475429e160865204acb129`.
- Recorded smoke budget: 100 batches, 10 inactive batches, 1,000 particles per batch.
- The script validates these data conditions before analysis.

## Methods

1. **Fixed-budget equal-allocation R&S baseline:** use the same 18 observations, with three observations per layout, and select the layout with the lowest sample mean of the dimensionless fission-rate-peaking proxy.
2. **CB-PFR:** reproduce the existing smoke-test heuristic with the same illustrative settings: (k_{eff}in[1.13,1.22]), fission-peaking proxy ≤ 2.0, uncertainty multiplier 2, and risk weight 1. These are illustrative software-test limits, not official C5G7 acceptance criteria or reactor safety limits.
3. **Exact QUBO selector:** enumerate all 64 binary selector states and verify a unique one-hot minimizer.
4. **Classical simulated quantum annealing (SQA):** run `dwave.samplers.PathIntegralAnnealingSampler` with 500 reads and 500 sweeps per read on that six-variable selector QUBO. This is a classical simulation, not a QPU run.

The R&S analysis is retrospective equal allocation, not adaptive sequential R&S. Because all OpenMC rows already exist, this run does not demonstrate adaptive allocation savings.

## Results

| Result | Observed |
|---|---:|
| R&S selected layout | **MUMU** |
| CB-PFR selected layout | **MUMU** |
| Selection agreement | Yes |
| Incremental CB-PFR selection gain demonstrated | **No** |
| Exact selector states enumerated | 64 |
| Exact QUBO minimizer | MUMU |
| SQA reads / sweeps per read | 500 / 500 |
| SQA best sample | MUMU, one-hot feasible |
| SQA best energy | −2.0 |
| SQA exact-ground-state hits | 143 / 500 (28.6%) |
| SQA one-hot samples | 497 / 500 (99.4%) |
| Best SQA energy matches exact minimum | Yes |

The current physical-data summary for the selected MUMU layout is mean (k_{eff}=1.14482492), between-seed SD (0.00216958), mean fission-peaking proxy (1.29626537), and between-seed SD of that proxy (0.02260486). These are descriptive results from the smoke-budget study, not a design recommendation.

## Interpretation

This experiment establishes that the code can run the retrospective equal-allocation R&S baseline, reconstruct the existing CB-PFR score, solve the six-variable selector QUBO exactly, and run a classical SQA sampler. The two selection rules chose the same layout. **The experiment therefore does not show that CB-PFR adds selection value over this R&S baseline.** It also does not prove CB-PFR is useless: the dataset is small, exploratory, and the R&S variant is non-adaptive.

The SQA sampler found the exact ground-state energy in this small selector problem, but that is not evidence of quantum hardware execution or quantum advantage. The six-variable selector is deliberately tiny and has an exact solution available.

## Limitations that remain open

- These are 100-batch / 1,000-particle exploratory OpenMC runs, not benchmark-grade convergence.
- The fission-peaking statistic is a dimensionless four-assembly proxy, not absolute power or a safety metric.
- No design-specific, authoritative (k_{eff}) acceptance band has been established for this altered layout set.
- The legacy `fresh / once_burned / twice_burned` QUBO still has no defensible mapping to the C5G7 UO₂/MOX layouts.
- The BEAVRS experimental spatial-map comparison remains poor; physical validation is not established.
- No actual quantum annealer/QPU job is archived; no quantum advantage claim is supported.

## Defensible conclusion

> On the archived corrected-group C5G7 smoke dataset, CB-PFR and a fixed-budget equal-allocation R&S baseline selected the same layout (MUMU). The current experiment demonstrates a reproducible comparison pipeline but does not establish incremental physical-ranking benefit for CB-PFR, benchmark-grade reactor validation, or quantum-hardware execution.

The next meaningful test is a pre-registered, adequately budgeted physical candidate study with justified constraints and an actual adaptive fixed-budget R&S policy, evaluated on fresh or held-out OpenMC results. Do not describe this report as a completed physical validation.
