# CB-PFR Post-Optimization Physical Feasibility: Deep Analysis Plan v1.0
**Date:** 2026-10-12  
**Purpose:** strengthen the core scientific claim that optimizer output is not, by itself, evidence of physical feasibility.  
**Relationship to freeze:** this is an analysis plan/addendum. It does not alter the frozen comparison protocol, current thresholds, or existing results.

## Core research question

Given a set of candidates produced by an optimizer, how should a downstream decision layer decide which candidates are physically admissible when physical-model outputs are uncertain, noisy, incomplete, or not yet independently validated?

The contribution is not that CB-PFR is universally better than QUBO. QUBO/optimizer and CB-PFR serve different roles:
- optimizer: generates or ranks candidates against its encoded objective/constraints;
- physical model: estimates behavior of each candidate under a specified model;
- CB-PFR: screens/ranks candidates using declared physical constraints and uncertainty information;
- independent validation: evaluates whether the physical model and its observables are credible for the intended application.

## Analysis A — prove the gap exists (highest priority)

### A1. Write a decision audit for each candidate
For every candidate, keep separate fields for:
1. optimizer feasibility and objective value;
2. physical-model outputs;
3. uncertainty provenance (Monte Carlo standard error, between-seed variation, reference/model uncertainty where available);
4. physical constraint status: PASS / FAIL / UNKNOWN;
5. CB-PFR status and reason;
6. missing/failed simulation status.

Do not merge UNKNOWN with PASS. A candidate with missing physical evidence is not physically verified.

### A2. Construct a transparent counterexample
Use an explicitly declared, independently justified physical constraint or a synthetic controlled example where the optimizer-optimal candidate fails the downstream constraint or has uncertainty that crosses the acceptance boundary, while another candidate remains admissible. Demonstrate the exact logic and preserve all values.

Important: the current C5G7 proxy values alone do **not** prove a physical-feasibility gap, because no accepted physical limits have been approved. Do not retrospectively invent a threshold to make CB-PFR reject the optimizer's winner. If a justified physical limit cannot be sourced, use a clearly labelled synthetic method test and keep it separate from the nuclear case study.

### A3. Report the right quantity
The central quantities are not simply “accuracy” or “winner score.” Report:
- fraction of optimizer candidates whose physical status is PASS / FAIL / UNKNOWN;
- false-acceptance rate: candidates declared admissible by the decision layer that fail the declared ground-truth/benchmark criterion;
- false-rejection rate: candidates rejected despite meeting that criterion;
- abstention/NO_SELECTION rate when evidence is insufficient;
- rank/selection stability under uncertainty perturbation.

For real physical data, these rates require a credible criterion/reference; otherwise report descriptive status counts only.

## Analysis B — test whether uncertainty handling is meaningful

### B1. Separate uncertainty sources
Do not collapse these into one standard deviation:
- within-run Monte Carlo uncertainty;
- between-seed/run variability;
- reference measurement or benchmark uncertainty;
- model-form and mapping uncertainty;
- parameter uncertainty.

The current 18 OpenMC runs provide repeated-seed information and per-run histories, but not a complete model-form uncertainty budget or signed benchmark review.

### B2. Sensitivity analysis
With a frozen candidate set and no post-hoc selection of favourable results, vary one declared uncertainty source at a time:
- uncertainty estimates within their defensible range;
- seed-round resampling;
- missing/failed run handling;
- declared bound multiplier z (sensitivity only, not post-hoc selection of the “best” z);
- constraint margin, only if justified externally or labelled illustrative.

For each perturbation, report whether the selected candidate changes, whether feasibility status changes, and how often CB-PFR abstains. Do not describe arbitrary z bounds as calibrated confidence intervals without coverage evidence.

### B3. Calibration test (synthetic controlled benchmark)
Use a transparent synthetic generator with known latent physical feasibility and controllable noise. Evaluate whether the uncertainty-aware screen's stated coverage/false-acceptance behaviour matches its claimed interpretation. Freeze generator, noise levels, criteria, sample size, and analysis before the confirmatory run. This tests method logic, not nuclear physics.

## Analysis C — interpret the existing C5G7 data without overclaiming

Existing high-budget evidence: six fixed layouts × three seed rounds; raw tally extraction reproduced the exported relative assembly-integrated fission-rate peaking proxy to floating-point precision.

Use it for:
1. a candidate-by-candidate uncertainty ledger;
2. per-layout distributions and intervals for keff and the relative fission-rate proxy;
3. rank stability across seed rounds / leave-one-round-out analysis;
4. a trace and inactive-source sensitivity plan for entropy and k-generation;
5. explicit separation between canonical benchmark case and non-canonical permutations.

Do not use the current relative fission-rate proxy as absolute power, a safety metric, or a physical acceptance criterion without a defensible mapping and justification. Do not infer “physically feasible” from low proxy alone. The canonical benchmark's scalar reference is applicable only to the exact canonical configuration and like-for-like model assumptions.

## Analysis D — physical-model credibility gate

Before a real nuclear feasibility claim, an independent reviewer should sign off:
- exact material-to-layout mapping and all reflector positions;
- geometry, boundaries, material temperature and cross-section data provenance/hash;
- tally score, mesh filter order/orientation, mesh-to-assembly mapping and normalization;
- source convergence protocol and inactive-batch sensitivity;
- benchmark applicability, observable correspondence, uncertainty/covariance assumptions;
- criteria and direction of improvement declared before ranking.

If this gate is unresolved, CB-PFR may report an evidence-aware status of UNKNOWN/INCONCLUSIVE, not a physically validated pass. This ability to abstain is a meaningful safety-of-decision feature, but it must be demonstrated by tests rather than asserted.

## Analysis E — compare roles, not slogans

The key ablation is:
- optimizer constraints/objective only;
- point-estimate physical screening;
- CB-PFR with uncertainty-aware screening.

Use the same candidate set, same data, same simulation budget, and same acceptance criteria. The comparison asks which decision-relevant information each layer adds, not whether CB-PFR replaces the optimizer. Include a predeclared tie policy because the current composition-only QUBO gives all six layouts the same energy.

## Suggested deliverables, in order

1. **Candidate evidence ledger** from the existing 18-run data, with no new simulations.
2. **Selection/rank stability analysis** across the three seed rounds, with explicit limitation that n=3 is exploratory.
3. **Synthetic counterexample and calibration benchmark** with known true feasibility, clearly separated from C5G7.
4. **Independent model/tally/convergence review** and justified physical acceptance criteria.
5. **Fresh confirmation seed rounds** only after criteria, model, and CB-PFR parameters are frozen.
6. **Final claim-to-evidence audit**: every claim marked supported / exploratory / unresolved / not supported.

## Claim wording

Recommended:
“CB-PFR is designed to bridge optimization and downstream physical evaluation by making feasibility status and uncertainty explicit during post-optimization candidate selection. The present C5G7 campaign demonstrates a reproducible evaluation path and exploratory candidate-ranking signals; physical feasibility criteria, model validation, and confirmatory decision performance remain under evaluation.”

Avoid:
- “CB-PFR proves the optimizer's solution is physically valid.”
- “CB-PFR is safer/better than QUBO.”
- “The lowest current fission-rate proxy is the safest or optimal reactor configuration.”
- “The model is physically validated” before the independent gate is passed.

## Non-negotiable methodological rule

A physically plausible result is not a validation criterion by itself. A reproducible simulation is not proof of model validity. A candidate ranking is not proof of physical feasibility. Keep these three claims separate.
