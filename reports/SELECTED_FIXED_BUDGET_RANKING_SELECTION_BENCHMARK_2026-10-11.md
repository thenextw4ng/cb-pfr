# Selected benchmark: fixed-budget ranking and selection under heteroscedastic uncertainty

**Decision date:** 2026-10-11  
**Status:** selected benchmark design; implementation and results are not yet claimed.  
**Primary purpose:** test the incremental *selection-method effect* of CB-PFR. This is not a nuclear-physics validation benchmark.

## Why this option

CB-PFR is a post-optimization ranking layer for a finite candidate pool. The closest methodological benchmark family is fixed-budget simulation **ranking and selection (R&S)**: choose the best alternative from noisy evaluations while controlling the evaluation budget. Gao, Xiao, Zhou, and Chen (Automatica, 2017) explicitly study robust ranking and selection under input uncertainty and a fixed simulation budget. This is a stronger conceptual match than a QUBO solver benchmark, which primarily compares optimization objective values rather than the quality of a downstream feasibility-aware selection.

Reference: https://doi.org/10.1016/j.automatica.2017.03.019  
Related data-driven fixed-budget R&S: https://doi.org/10.1287/ijoo.2024.0035

## Benchmark definition

### Candidate pools and known truth

- Generate independent finite pools of 12 candidates, matching the current CB-PFR experiment's pool size.
- Each candidate has a fixed latent objective and one or more latent physical-feasibility metrics. The generator exposes these latent values only to the evaluator, never to the selection methods.
- Include both clearly feasible/infeasible cases and near-boundary candidates, so feasibility screening can discriminate.
- Use candidate-specific, heteroscedastic observation noise. Predeclare at least three regimes: low, moderate, and high noise; include a regime where uncertainty estimates are calibrated and a stress regime where they are mildly misspecified.
- Use a fixed, equal observation budget for each method and candidate pool. The evaluator's latent truth is held out from method selection.

### Methods compared on the same pools

1. **QUBO-only:** choose the lowest-energy QUBO-feasible candidate; specify in advance how QUBO energy relates (or deliberately does not relate) to latent physical quality.
2. **Point estimate:** rank using noisy observed means and nominal feasibility thresholds, without uncertainty margins.
3. **CB-PFR:** use the existing implementation and frozen lexicographic selection key, with candidate-specific operational uncertainty bounds.
4. **Uniform-margin baseline:** use one common margin tuned on development pools only, then frozen for confirmation.

All methods receive identical candidate identities, raw observation streams where applicable, and total evaluation budgets. No method may see latent truth during selection. Do not tune the CB-PFR risk parameter on confirmatory pools.

## Primary and secondary endpoints

**Primary endpoint:** reference-evaluated feasible-selection rate: fraction of independent pools where the method's selected candidate satisfies the predeclared latent feasibility rule.

Secondary endpoints:
- false-feasible rate: selected candidate is declared feasible by the method but is infeasible under latent truth;
- feasible-best selection rate, conditional on at least one feasible candidate existing in the pool;
- objective regret versus the best latent-feasible candidate in that pool;
- latent constraint-violation magnitude;
- no-feasible-selection rate;
- sensitivity to noise level and uncertainty miscalibration.

Report each endpoint with numerator/denominator and 95% intervals. Use the pool as the independent unit. Compare methods with paired differences on the exact same pools; do not count repeated observations within a pool as independent trials.

## Split, replication, and decision rule

- Development: 200 pools for checking implementation and freezing any baseline settings.
- Confirmatory: 1,000 independently generated pools with seeds frozen before execution.
- Do not mix development and confirmatory results.
- Report paired CB-PFR minus point-estimate and CB-PFR minus uniform-margin differences on the primary endpoint, with 95% paired bootstrap intervals.
- A superiority claim requires the paired interval to exclude zero in CB-PFR's favor against **both** point estimate and uniform margin on the primary endpoint, with no hidden exclusions and all noise regimes reported.
- If the gate is not met, report no demonstrated advantage. If results depend on one noise regime, restrict the claim to that regime.

The 1,000 confirmatory pools are a proposed design target, not evidence that these runs have already occurred. A pilot/power analysis should be used to refine the count before locking compute allocation.

## Integrity and reproducibility requirements

- Store one row per pool-method selection and a separate trial-level candidate observation table.
- Include pool ID, seed, candidate ID, latent truth (in evaluator-only table), observed mean, uncertainty estimate, method, chosen candidate, predicted feasibility, true feasibility, budget, noise regime, and code/configuration hashes.
- Keep evaluator-only truth separate from method input files to prevent leakage.
- Include tests for equal budgets, truth leakage, invalid metrics, deterministic replay, and correct paired analysis.
- Archive the full configuration, seed list, trial-level CSV, summary CSV, and reproduction command.

## What this benchmark can and cannot establish

A positive result can support a bounded statement such as: “Under the prespecified fixed-budget ranking-and-selection data-generating process, CB-PFR improved reference-evaluated feasible-selection rate over the named baselines.”

It **cannot** establish that C5G7 or BEAVRS is physically validated, that CB-PFR improves reactor safety/performance, or that synthetic uncertainty matches nuclear transport/experimental uncertainty. Those require separate nuclear-physics evidence.

## Why not increase C5G7 runs first?

The current C5G7 smoke dataset has six layouts and three seeds per layout; its mean-based and illustrative mean-plus-standard-deviation rankings select the same candidate. All six pass the illustrative screening gates, which are not authoritative reactor acceptance criteria. More transport runs may reduce Monte Carlo uncertainty but do not by themselves create discriminating feasibility labels or prove a CB-PFR treatment effect. Return to C5G7 after this method benchmark and after freezing a defensible physical objective and acceptance rule.
