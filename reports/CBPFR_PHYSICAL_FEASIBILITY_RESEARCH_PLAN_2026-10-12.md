# CB-PFR Physical Feasibility Research Plan — Beyond Optimizer Superiority
**Date:** 2026-10-12  
**Purpose:** Focus the next research phase on the gap between mathematical optimization and evidence-based physical feasibility. This plan is separate from, and does not rewrite, the frozen comparison protocol v1.0.

## Central research question

When an optimizer returns a mathematically feasible candidate, what additional evidence is required before that candidate can be considered physically admissible under uncertain simulation outputs, and can CB-PFR make that decision more explicit, uncertainty-aware, and reproducible?

The primary claim is **not** that CB-PFR is a better optimizer than QUBO. QUBO is a problem formulation/optimization approach; CB-PFR is a downstream feasibility/ranking layer. The methods have different roles and should not be framed as interchangeable competitors.

## Core conceptual distinction

Keep three statuses separate:
1. **Mathematically feasible:** satisfies the encoded variables and constraints.
2. **Physically accepted:** satisfies predeclared, scientifically justified physical criteria under an audited model and uncertainty treatment.
3. **Inconclusive:** the available evidence cannot establish acceptance or rejection.

A missing criterion, unresolved model mapping, or inadequate uncertainty estimate must not silently become a pass. An inconclusive status is a legitimate output, not a failure of the method.

## Research avenue 1 — Mathematical-feasibility / physical-evidence gap

### Question
Among candidates that satisfy the encoded optimization constraints, how many can be physically accepted, rejected, or remain inconclusive under an independently justified physical rule?

### Analysis
- Freeze the candidate set and map each candidate to the exact physical model inputs.
- Have the physical endpoint(s), acceptance limits, reference case, and uncertainty treatment reviewed before candidate ranking.
- Report counts and identities in the three categories: accepted, rejected, inconclusive.
- Report reasons for each non-accepted candidate (measured violation versus insufficient evidence).
- Never infer physical failure solely from not matching a canonical benchmark value when the candidate is a different configuration.

### Current limitation
The six C5G7 layouts meet the same two-MOX composition constraint, but there is not yet an approved physical acceptance rule for all six. The current fission-rate peaking value is a proxy, not a universal safety criterion. Thus the current data demonstrate that QUBO composition feasibility does not itself rank the physical proxy; they do not yet quantify a validated physical-feasibility gap.

## Research avenue 2 — Uncertainty-aware decision stability

### Question
Does the decision based on point estimates change when uncertainty is included, and how often is the evidence insufficient for a robust decision?

### Analysis
- Use current three seed rounds only for exploratory analysis.
- For every candidate and metric, separate within-run Monte Carlo uncertainty from between-seed variation.
- Compare point-estimate ranking with CB-PFR conservative-bound screening.
- Conduct a declared sensitivity analysis over plausible uncertainty multipliers and scientifically justified physical limits; label any unapproved limit as illustrative only.
- Report selection changes, status changes, tie rates, and inconclusive rates.
- Do not call arbitrary mean ± z·SD bounds calibrated confidence intervals without a coverage argument.

### What would be informative
A result where the point-estimate choice changes under uncertainty is a concrete example of why nominal optimization is not enough. A result where the choice remains unchanged is also useful: it indicates robustness within the examined uncertainty model, not universal physical validity.

## Research avenue 3 — Repeatability and held-out confirmation

### Question
Does the selection rule remain stable on new, independent simulation runs rather than only on the data used to design it?

### Analysis
- Treat existing three seed rounds as exploratory/training data.
- Freeze code, candidate mapping, metrics, uncertainty calculation, physical rule, and tie policy.
- Run fresh seed rounds with identical per-candidate settings and preserve all runs, failures, and logs.
- Report selection consistency, uncertainty intervals, and the frequency of accepted/rejected/inconclusive outcomes.
- Keep convergence and benchmark-model review as independent gates.

### Limitation
Three seed rounds are too few to make a strong generalization claim. More runs should be chosen based on a declared precision/power target and computational budget, not an arbitrary claim that a particular small number is enough.

## C5G7 data already in hand

The high-budget campaign in GitHub Actions run 38229045726 has six layouts × three seed rounds (18 statepoints). The exported relative assembly-integrated fission-rate peaking proxy was reconstructed from raw statepoints to a maximum absolute discrepancy of 2.22e-16. This confirms extraction/arithmetic consistency only.

Descriptive means from the current campaign:

| Layout | Mean k-effective | Mean relative fission-rate peaking proxy |
|---|---:|---:|
| MMUU | 1.1436721 | 1.2953689 |
| MUMU | 1.1437002 | 1.2963641 |
| MUUM | 1.1562627 | 1.3161492 |
| UMMU | 1.1864986 | 1.8671004 |
| UMUM | 1.2046883 | 1.8167198 |
| UUMM | 1.2046416 | 1.8160915 |

The proxy is not absolute power or a safety metric. MMUU is only the current descriptive minimum for this proxy; it is not certified as the physically optimal or safest layout. The canonical scalar reference applies only to the exact canonical case, not all permutations.

## Important implementation distinction

The composition-only QUBO objective A*(sum(y_i)-2)^2 ties all six two-MOX candidates. That is a composition constraint, not a physics-aware optimizer. The right question is therefore not "does CB-PFR beat QUBO at optimization?" but "what evidence and decision discipline does CB-PFR add after an optimizer has proposed candidates?"

For a meaningful method study, compare:
- point-estimate selection;
- uncertainty-aware CB-PFR screening;
- a predeclared no-information/tie policy where appropriate.

Use equal information and evaluation budgets. Include a genuinely physics-aware optimizer only if its objective and mapping are defined independently and fairly.

## Preregistered claim boundary

### Claim allowed now
"CB-PFR is a proposed uncertainty-aware post-optimization feasibility and ranking layer intended to distinguish mathematical candidate feasibility from evidence-supported physical admissibility. A C5G7/OpenMC screening campaign demonstrates an executable candidate-evaluation path and reproducible extraction of a relative fission-rate proxy; physical acceptance criteria, full convergence certification, and independent model/tally review remain pending."

### Claim not allowed now
- "CB-PFR proves that the selected layout is physically safe/optimal."
- "CB-PFR has validated the reactor model."
- "CB-PFR is statistically superior to QUBO or all alternatives."
- "The relative fission-rate proxy is absolute power."
- "All six configurations are physically feasible because they pass the illustrative screen."

## Immediate work order

1. Audit the implemented CB-PFR ranking and uncertainty semantics against the code and tests; verify that documented bounds and ranking order exactly match implementation.
2. Audit the C5G7 physical mapping, assembly indexing, tally meaning, source convergence, and canonical benchmark applicability with an independent reviewer.
3. Choose the physical endpoint and criteria with a defensible scientific rationale before using the candidates to claim acceptance.
4. Run exploratory uncertainty/decision-stability analysis on existing seeds, with all thresholds clearly labelled illustrative until justified.
5. Freeze the final protocol and test it on fresh independent seed rounds. Do not use confirmation results to tune the method.
6. Report accepted, rejected, and inconclusive decisions separately, including uncertainty and compute cost.

## Related records

- Frozen comparison protocol: protocol/CBPFR_METHOD_AND_COMPARISON_FREEZE_v1.0_2026-10-12.md
- Direct comparison: reports/CBPFR_VS_QUBO_ONLY_DIRECT_COMPARISON_2026-10-12.md
- Raw statepoint audit: reports/CBPFR_RAW_STATEPOINT_AUDIT_2026-10-12.md
- Source/convergence audit: reports/CBPFR_PRIMARY_SOURCE_AND_CONVERGENCE_AUDIT_2026-10-12.md
- Claim-to-evidence matrix: reports/EUREKA_CLAIM_EVIDENCE_MATRIX_2026-10-11.md
