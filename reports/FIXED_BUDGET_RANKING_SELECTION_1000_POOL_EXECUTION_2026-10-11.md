# Fixed-budget Ranking-and-Selection: 1,000-pool execution record

**Run date:** 2026-10-11  
**Status:** A 1,000-pool synthetic execution was run locally using the repository's existing exploratory script logic. This is an extended exploratory run, **not yet the preregistered final confirmatory benchmark**.  
**Physical validation:** `NOT_ESTABLISHED`

## Design
- 1,000 candidate pools, 12 candidates per pool, seed `20261011`.
- Feasibility threshold 0.98; CB-PFR-style (z=1.96); uniform margin 0.008.
- Four methods: QUBO-energy-only, point estimate, candidate-specific CB-PFR-style margin, uniform margin.
- Same candidate pool and pool size for all methods; synthetic latent response used for scoring.
- Toy DGP: latent response (0.954 + 0.013\times\text{fresh_pairs} + 0.002\times\text{arrangement}), with candidate-specific standard error 0.004 or 0.010.

## Results

| Method | Selected truly feasible | Mean selected latent response |
|---|---:|---:|
| QUBO-energy-only | 83.4% (834/1,000) | 0.967833 |
| Point estimate | 91.8% (918/1,000) | 0.964736 |
| CB-PFR-style bound | **99.4% (994/1,000)** | 0.960052 |
| Uniform margin | 95.9% (959/1,000) | 0.961568 |

## Paired difference: CB-PFR-style minus baseline

| Baseline | Difference | Approx. 95% normal interval | CB-PFR wins / loses |
|---|---:|---:|---:|
| Point estimate | +7.6 percentage points | [+5.91, +9.29] pp | 78 / 2 |
| Uniform margin | +3.5 percentage points | [+2.33, +4.67] pp | 36 / 1 |
| QUBO-energy-only | +16.0 percentage points | [+13.68, +18.32] pp | 163 / 3 |

Intervals are paired, pool-level normal approximations; they are not multiplicity-adjusted. The result is conditional on this deliberately simple toy data-generating process and should not be generalized to other distributions without testing.

## What this does and does not establish
This run provides an executable, larger-scale synthetic result that is directionally consistent with the 200-pool exploratory record. It **does not by itself establish general algorithmic effectiveness** because the DGP is simple and selected for illustration, uncertainty calibration has not been stress-tested, and the run is not an independent replication. It does not establish physical/reactor effectiveness. The C5G7/BEAVRS physical gate remains `NOT_ESTABLISHED`.

## Required next gates
1. Add an independently implemented test harness and test edge cases / invariants.
2. Freeze a preregistration including primary endpoint, meaningful effect threshold, stress scenarios, and analysis plan before confirmatory runs.
3. Evaluate calibrated and miscalibrated uncertainty, heteroscedasticity, shifted distributions, no-feasible pools, and sensitivity to (z)/uniform margin.
4. Independently reproduce the run from a clean checkout and verify raw per-pool CSV against aggregates.
5. For physical claims, resolve QUBO-to-geometry/material mapping and benchmark-grade model/observable convergence before interpreting reactor results.

