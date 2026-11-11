# OpenMC low-cost smoke run: observed result

**Execution status:** completed successfully in GitHub Actions on 2026-10-11.  
**Workflow:** [run 38122348349](https://github.com/thenextw4ng/cb-pfr/actions/runs/38122348349)  
**OpenMC:** 0.15.3  
**Physical validation:** `NOT_ESTABLISHED`

## Run configuration and observed output

| Item | Observed value |
|---|---:|
| Model | OpenMC Python API C5G7-derived 2×2 multigroup lattice example |
| Batches | 20 |
| Inactive batches | 5 |
| Particles per batch | 500 |
| Threads | 2 |
| Reported (k_{eff}) | 1.31327333 |
| OpenMC-reported standard deviation | 0.00981881 |
| Ranking-rule (z) | 1.96 |
| Ranking threshold used in the smoke script | 1.0 |
| CB-PFR-style selected label | `replicate_A` |

The low-cost run completed in under a second of transport time after environment setup. These settings were deliberately selected for a software smoke test, not for convergence.

## What this result validates
- OpenMC 0.15.3 installed in the GitHub Actions environment.
- The bundled C5G7-derived multigroup lattice example ran to a statepoint in eigenvalue mode.
- The script read the reported (k_{eff}) and uncertainty and executed the CB-PFR-style lexicographic ranking code.
- The workflow archived the run inputs and JSON result.

## What it does not validate
The (k_{eff}) value is **not presented as a canonical C5G7 benchmark result**; this example/configuration is not the full reference benchmark, and the smoke-test particle budget is too small for benchmark-quality inference. Do not compare it directly with a canonical C5G7 reference or infer model accuracy.

The three ranked labels in the script are artificial perturbations of the same (k_{eff}) estimate, not distinct physical candidate configurations. Thus, this run does **not** test whether CB-PFR selects a better physical design than point-estimate, QUBO-only, or uniform-margin methods. The threshold of 1.0 is a plumbing value, not a validated engineering acceptance limit.

## Verdict
**OpenMC integration smoke test: PASS.**  
**CB-PFR/R&S physical-effectiveness validation: NOT ESTABLISHED.**

To make a physical claim, the next experiment must define distinct candidate geometries/materials and a defensible QUBO-to-physics mapping, freeze the objective and feasibility criteria, run independent replicates at equal budgets, use held-out simulations to score selected candidates, and demonstrate benchmark convergence.
