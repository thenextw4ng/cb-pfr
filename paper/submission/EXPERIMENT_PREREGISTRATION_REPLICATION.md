# Preregistered follow-up: replication and decision-rule calibration

Status: **protocol only; no new OpenMC runs or outcomes are represented here**.

This document freezes the proposed design before any follow-up simulation. It is not evidence that the experiment has run. The archived 18-run campaign and the two three-seed UMMU protocols remain separate historical datasets.

## Questions

1. Do uncertainty-expanded per-candidate bounds improve empirical classification near a declared feasibility boundary relative to point estimates and a common fixed margin?
2. Is any improvement concentrated near the boundary, as expected for a conservative screening rule?
3. Do symmetry-related labels retain ties when the evidence does not distinguish them?

## Reference target

The reference is the long-run *model estimate* for each representative layout/class, based on 7,000 total OpenMC batches. It is not physical truth, a validated C5G7 benchmark result, or an engineering acceptance standard. The existing 100-inactive-batch UMMU protocol is ineligible as a canonical reference until the entropy mesh covers all fissionable material and the repeated out-of-mesh warnings are absent. The 500-inactive-batch protocol also requires a predeclared convergence review; neither archived protocol is certified by this document.

## Gate 0: source/model readiness

Before spending replication compute, record and review:
- geometry/material mapping and tally-to-fuel-region correspondence against the model specification;
- entropy mesh bounds and a check that no fission-source sites fall outside the mesh;
- independent, non-overlapping seed streams and distinct initial source states where appropriate;
- statepoint and input hashes, OpenMC version, particle/batch counts, inactive batches, thread count, and elapsed time;
- predeclared convergence criteria for active-batch k-generation and source-entropy traces.

If any required audit fails, stop and label the run set diagnostic-only. Do not silently omit failed runs or tune criteria after seeing the result.

## Replication design

After Gate 0 passes, simulate representatives MMUU, MUUM, UMMU, and UMUM. Preserve raw run-level outputs and use independently generated seeds. First conduct a timing pilot and freeze the feasible run budget. The intended target is R=200 independent short runs per representative and per chosen budget, but the actual R must be declared before the first scored replication and may be reduced only before outcomes are inspected. If the compute budget cannot support the target, label the experiment underpowered and report the achieved R.

For every run, store the four assembly-integrated fission tallies, the derived F=max(R_i)/mean(R_i), keff estimate and uncertainty, source entropy and k-generation traces, convergence flags, runtime, seed, and hashes. Since F is a ratio involving a maximum, note its finite-sample upward bias; estimate uncertainty from independent run-level F values for between-run comparisons. Do not treat correlated tallies within one run as independent replications.

## Decision rules fixed before scored runs

- R0: point-estimate feasibility-first ranking.
- R1: the same fixed absolute margin for every class, selected from a separate pilot or external rationale and frozen before scored runs.
- R2: CB-PFR operational upper bound with z=1.
- R3: CB-PFR operational upper bound with z=2.

For the fission peaking proxy, evaluate boundary-distance scenarios d=(F_max-F_reference)/sigma_short in {0.5, 1, 2, 4}. These are controlled sensitivity scenarios, not post hoc choices of a threshold that makes one method look best. Also report the naturally observed class-dependent spread (heteroskedasticity) without rescaling results to favor a rule. Keep the k criterion distinct and state whether it is active in each scenario.

## Outcomes and analysis

Primary outcomes:
- false-accept and false-reject rates against the declared long-run model-reference labels;
- empirical coverage of the operational bounds (clearly distinguished from calibrated confidence intervals);
- retention of ties for symmetry-related labels;
- top-1 stability and Kendall's tau between replicate rankings and reference ranking.

Report Wilson intervals for rates and the achieved sample size in every cell. Report the full confusion matrix and all exclusions. Compare rules on the same runs. Do not describe the model-reference labels as physical truth. Do not claim that CB-PFR always wins; a null result or an effect restricted to near-boundary cases is valid.

## Stop conditions and reporting

Stop and mark the replication experiment inconclusive if source-convergence review fails, entropy-mesh warnings persist, seeds are not independent, required tallies are missing/non-finite, or the reference label is unstable under the predeclared convergence review. Publish the preregistration hash and source commit before the scored experiment. Report deviations with dates and reasons; do not amend this document retrospectively to fit observed outcomes.

## Current blockers

- OpenMC is not installed in the current artifact-building environment.
- No corrected entropy-mesh model inputs and raw source files are present in the anonymous supplement.
- Consequently, this protocol has **not** been executed, and no replication outcomes, error rates, or calibrated coverage claims are available.
