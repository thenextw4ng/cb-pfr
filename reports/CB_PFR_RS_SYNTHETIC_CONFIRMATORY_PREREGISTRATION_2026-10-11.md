# CB-PFR vs fixed-budget R&S: locked synthetic confirmatory protocol

**Protocol version:** 1.0  
**Lock date:** 2026-10-11  
**Branch:** `research/fixed-budget-ranking-selection-benchmark`  
**Status:** `PREREGISTERED_PROTOCOL_PENDING_EXECUTION`  
**Scope:** algorithmic comparison under synthetic ground truth only. This protocol does not establish reactor-physics validity.

## 1. Research question

Under a fixed candidate-pool size and the same observed estimates, does uncertainty-aware CB-PFR-style screening improve the probability that the selected candidate is truly feasible, compared with point-estimate selection and a fixed uniform-margin baseline?

This is a synthetic algorithm benchmark. Results must not be described as proof of universal effectiveness or physical/reactor effectiveness.

## 2. Locked design

- Independent pools: 10,000 per scenario.
- Candidates per pool: 12.
- Base seed: 20261013; each scenario uses a deterministic, documented offset from this seed.
- Feasibility threshold: latent response \(\theta_i \ge 0.98\).
- CB-PFR-style one-sided screen: \(\hat\theta_i - 1.96\,s_i^{reported} \ge 0.98\).
- Uniform-margin screen: \(\hat\theta_i - 0.008 \ge 0.98\).
- Point-estimate baseline: candidates ranked by \(\hat\theta_i\), without uncertainty screening.
- QUBO-only baseline: use only the prespecified candidate energy/rank signal; do not give this baseline uncertainty information.
- Within each method, if at least one candidate passes its screen, select the passing candidate with the largest observed estimate. If none pass, use the candidate with the largest corresponding lower-bound score (CB-PFR), largest uniform-margin score (uniform margin), or largest observed estimate (point estimate). Ties are resolved by candidate index.
- All methods receive the same pool and observed estimates. No method-specific pool filtering.
- Do not change thresholds, scenarios, metrics, or seeds after inspecting results.

## 3. Prespecified data-generating scenarios

Each pool has 12 candidates. Latent responses are generated independently of method selection; reported standard errors are candidate-specific and observations are noisy estimates of the latent response. Use four scenario families:

1. **Calibrated heteroscedastic:** standard errors vary across candidates and reported standard errors match the data-generating noise scale.
2. **Calibrated homoscedastic:** one common noise scale for all candidates; reported standard errors are calibrated.
3. **Underreported uncertainty:** same latent/noise construction as scenario 1, but reported standard errors are multiplied by 0.5.
4. **Shifted / near-threshold:** latent responses are concentrated around the 0.98 feasibility threshold and observations include a prespecified +0.008 shift. This is a stress case, not a calibrated physical model.

Document exact distributions and parameters in the executable script before running the locked experiment. No scenario may be removed because its result is unfavorable.

## 4. Endpoints and analysis

### Primary endpoint
Per scenario, the selected candidate's true-feasibility indicator \(I(\theta_{selected}\ge0.98)\). Report the absolute paired percentage-point difference for CB-PFR minus each baseline, based on the same pools.

### Secondary endpoints
- False-feasible selection rate: selected candidate is declared feasible by the method but \(\theta_{selected}<0.98\).
- Feasible-best selection: selected candidate is the highest-latent-response candidate among truly feasible candidates, where at least one feasible candidate exists.
- Regret: best feasible latent response minus selected latent response when a feasible candidate exists; separately flag infeasible selections.
- Coverage/calibration: empirical coverage of nominal one-sided lower bounds, reported by uncertainty stratum.
- No-feasible-pool frequency and fallback-selection frequency.

### Uncertainty and multiplicity
Report paired differences with paired bootstrap 95% confidence intervals (resample pools, not candidates). The two primary CB-PFR comparisons (point estimate and uniform margin) form one family; apply Holm correction to the two two-sided tests. Report raw and adjusted p-values. Include counts and denominators. Do not use unpaired standard errors for paired outcomes.

## 5. Decision rule

Call a synthetic advantage **supported for this prespecified scenario family** only if:
1. the CB-PFR selected-feasibility difference is positive against both point estimate and uniform margin in the pooled primary analysis;
2. the paired 95% confidence interval excludes zero for both comparisons after the prespecified multiplicity procedure; and
3. the observed absolute improvement is at least 2 percentage points against each baseline.

If any criterion fails, report that the confirmatory benchmark did not establish the prespecified advantage. Scenario-specific wins do not override a failed pooled primary endpoint. Do not use the word “universal,” “physically validated,” or “reactor-safe.”

## 6. Reproducibility and audit gates

- Save per-pool/per-candidate truth, estimate, reported standard error, selected candidate for each method, and method-declared feasibility to CSV.
- Save a JSON summary with seed, scenario parameters, package/runtime versions, metrics, confidence intervals, raw/adjusted p-values, and SHA-256 hashes of raw outputs and script.
- Run from a clean checkout and compare regenerated summaries with committed artifacts.
- Include automated tests for threshold equality, no-feasible pools, all-feasible pools, underreported uncertainty, deterministic tie-breaking, and reproducible seeds.
- Keep the existing 1,000-pool and six-scenario runs labeled exploratory. This protocol does not retroactively convert those results into confirmatory evidence.

## 7. Claim boundary

Even if all decision criteria pass, the conclusion is limited to the locked synthetic scenario family and implementation. It does not establish performance on real OpenMC results, general algorithmic superiority, a valid QUBO-to-reactor mapping, or physical reactor validity. Physical claims are outside this protocol and remain `NOT_ESTABLISHED`.

## 8. Execution record

- Execution status: `PENDING`
- Raw output: pending
- Summary JSON: pending
- Clean-checkout reproduction: pending
- Independent review: pending
