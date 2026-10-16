# Exploratory Fixed-Budget Ranking-Selection Run — 2026-10-11

**Status: exploratory synthetic run recorded. Physical validation remains NOT ESTABLISHED.**

## Setup
- Seed: 20261011
- 200 independent pools, 12 candidates per pool
- Four methods: QUBO-only, point estimate, CB-PFR-style uncertainty bound, uniform margin
- Equal pool information and evaluation budget for all methods
- Synthetic feasibility threshold 0.98; uncertainty multiplier z=1.96; uniform margin 0.008
- Python standard library only; no expensive simulation

The toy generator assigns each candidate a latent response from simple discrete attributes, then adds Gaussian observation noise. The selection rule sees the noisy estimate and reported standard error; latent truth is used only to score the selected candidate. This is a deliberately simplified mathematical experiment, not a physical model.

## Results

| Method | Selected true-feasibility rate | Mean selected latent response |
|---|---:|---:|
| QUBO-only | 0.860 | 0.96659 |
| Point estimate | 0.930 | 0.96418 |
| CB-PFR-style bound | 0.995 | 0.95966 |
| Uniform margin | 0.960 | 0.96138 |

Paired difference in selected feasibility rate (CB-PFR-style minus baseline), using simple normal-approximation 95% intervals:

| Baseline | Difference | Approx. 95% interval |
|---|---:|---:|
| Point estimate | +0.065 | [+0.0307, +0.0993] |
| Uniform margin | +0.035 | [+0.0095, +0.0605] |
| QUBO-only | +0.135 | [+0.0875, +0.1825] |

## Limits
These results apply only to this constructed toy distribution. They do not establish general superiority, physical validity, or effectiveness on any reactor or transport model. The run is exploratory and is not the planned confirmatory 1,000-pool benchmark. The intervals are approximate and should not replace a prespecified confirmatory analysis.

## Reproduce
From repository root:

```bash
python scripts/run_fixed_budget_ranking_selection_exploratory.py
```

The script writes per-pool outcomes and a JSON summary under `results/fixed_budget_ranking_selection_exploratory/`.
