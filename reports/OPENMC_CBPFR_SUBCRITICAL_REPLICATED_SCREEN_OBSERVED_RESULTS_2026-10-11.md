# Observed results: OpenMC CB-PFR subcriticality replicated screen (2026-10-11)

**Result status: completed exploratory OpenMC screen; physical validation of CB-PFR remains NOT ESTABLISHED.**

Run: https://github.com/thenextw4ng/cb-pfr/actions/runs/38123032286  
Artifact: `openmc-cbpfr-subcriticality-replicated-screen` (25 raw OpenMC runs, summary JSON, held-out policy CSV).  
OpenMC 0.15.3; conventional eigenvalue mode was used. The bundled example's random-ray settings were explicitly cleared before exporting model settings.

## Experimental budget
Five configurations × five independent seeds = 25 runs. Each run used 20 batches, 6 inactive batches, 500 particles/batch, two threads. This is deliberately low-cost and statistically limited.

## Observed results

| Configuration | Mean (k_{eff}) | Between-seed SD | OpenMC-reported SD (mean) | Runs below 1.0 |
|---|---:|---:|---:|---:|
| Four fuel positions | 1.32026 | 0.00899 | 0.00806 | 0/5 |
| Three fuel positions | 1.31150 | 0.01535 | 0.00952 | 0/5 |
| Two adjacent fuel positions | 1.15700 | 0.01820 | 0.01053 | 0/5 |
| Two diagonal fuel positions | 1.20728 | 0.01195 | 0.01013 | 0/5 |
| One fuel position | 0.83808 | 0.01017 | 0.00904 | 5/5 |

The five leave-one-seed-out folds selected `one_fuel` under all three policies:
- Point-estimate policy: 5/5 held-out runs below 1.0; mean held-out (k_{eff}=0.83808).
- CB-PFR-style upper-bound policy: 5/5; mean held-out (k_{eff}=0.83808).
- Uniform +0.02 margin: 5/5; mean held-out (k_{eff}=0.83808).

## Interpretation

1. The code successfully simulated five distinct fuel/moderator arrangements and preserved per-run statepoints/results.
2. For this toy geometry and illustrative threshold (k_{eff}<1.0), the one-fuel configuration was clearly separated from the others and was selected by every policy.
3. **This is not evidence that CB-PFR outperforms point estimates or uniform margins.** The selected candidate never differed across policies; the candidate pool made the decision easy. Five folds are also too few to support a general effectiveness claim.
4. The earlier run that retained `<random_ray>` in the settings is not used for these results; this corrected run confirms the exported settings contain no random-ray block.
5. The between-seed standard deviation is descriptive. With only five seeds, (ar{k}+1.96s) is an operational screen, not a calibrated 95% confidence bound.
6. (k_{eff}<1) alone does not certify reactor safety or design acceptability. This is an OpenMC bundled C5G7-derived 2×2 lattice example, not a canonical C5G7 benchmark validation.

## What remains to establish physical CB-PFR validity

- A defensible mapping from QUBO variables/constraints and candidate IDs to physically meaningful configurations is still absent. We therefore do not report a QUBO-only baseline or claim that this is a physical QUBO-generated candidate pool.
- A target observable and acceptance rule must be justified for the intended application; (k_{eff}<1) here is only an illustrative subcriticality screen.
- Benchmark verification and adequate convergence/uncertainty analysis are still needed.
- A fair method-effectiveness study must use a candidate pool where policies can make different selections, equal information budgets, and independent held-out scoring. The present experiment produced identical selections and therefore no measured CB-PFR advantage.

## Final classification

`OPENMC_EXECUTION_VALIDATED_FOR_THIS_TOY_SCREEN`  
`PHYSICAL_CB_PFR_VALIDATION: NOT_ESTABLISHED`  
`GENERAL_CB_PFR_SUPERIORITY: NOT_DEMONSTRATED`
