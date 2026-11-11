# Fixed-budget R&S stress/sensitivity run (exploratory)

**Run date:** 2026-10-11  
**Status:** Executed locally, 1,000 pools per scenario, 12 candidates per pool.  
**Physical validation:** `NOT_ESTABLISHED`

## Design
Six hand-specified synthetic scenarios were run with seed base `20261012`, threshold 0.98, CB-PFR-style (z=1.96), and uniform margin 0.008. Scenarios: heteroscedastic baseline, homoscedastic noise, reported uncertainty halved, reported uncertainty doubled, observation shift +0.008, and a near-threshold latent-response variant.

## Selected true-feasibility rate

| Scenario | QUBO only | Point estimate | CB-PFR-style | Uniform margin |
|---|---:|---:|---:|---:|
| Heteroscedastic baseline | 82.4% | 91.2% | 99.6% | 96.4% |
| Homoscedastic | 83.4% | 91.5% | 99.6% | 97.0% |
| Uncertainty underreported by 50% | 84.9% | 92.5% | 97.2% | 96.1% |
| Uncertainty overreported 2x | 82.1% | 89.6% | 100.0% | 95.0% |
| Observation shift +0.008 | 86.3% | 95.6% | 99.9% | 98.9% |
| Near-threshold variant | 84.0% | 87.5% | 98.1% | 91.8% |

## Interpretation
CB-PFR-style selection had the highest selected-feasibility rate in these six toy scenarios. Underreported uncertainty reduced its rate from the base case, which is directionally consistent with the method relying on credible uncertainty estimates. This is not evidence of universal superiority: the scenarios are few, hand-specified, and share a simple synthetic structure. No external or physical model was tested, and the study does not yet provide a complete preregistered statistical confirmation.

## Required follow-up
A defensible confirmatory benchmark should be preregistered before running the final data, include broad independently generated data-generating processes, evaluate uncertainty calibration, false-feasible rates, feasible-best selection and regret, set a practically meaningful effect threshold, and have an independent clean-checkout reproduction. Reactor effectiveness remains a separate gate.
