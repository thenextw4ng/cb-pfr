# CB-PFR Method and Comparison Freeze Specification v1.0
**Freeze date:** 2026-10-12  
**Repository:** thenextw4ng/cb-pfr  
**Status:** protocol freeze for the next confirmatory comparison; not a declaration of physical validation or algorithmic superiority.

## 1. Purpose and scope

Freeze the scientific question, method roles, comparison baselines, outcomes, and claim boundaries before inspecting new confirmatory runs. Two separate tracks must not be conflated:

- **Method track:** Does the CB-PFR uncertainty-aware post-optimization ranking layer improve candidate selection under a declared data-generating process?
- **C5G7 physical-screen track:** What do the six fixed UO2/MOX layouts show under the current OpenMC model and relative assembly-integrated fission-rate peaking proxy?

The physical-screen track is exploratory until model/tally review, source-convergence review, and physically justified acceptance criteria are signed off.

## 2. Frozen definition of CB-PFR

CB-PFR is a post-optimization ranking/feasibility layer, not a new QUBO optimizer and not a reactor-safety method.

For candidate i and metric j, retain the implemented interval-style screening definitions:
- lower/upper uncertainty bounds: B^-_{i,j} = mu_hat_{i,j} - z_j s_hat_{i,j}, B^+_{i,j} = mu_hat_{i,j} + z_j s_hat_{i,j};
- violation: v_{i,j} = max(0, L_j - B^-_{i,j}) + max(0, B^+_{i,j} - U_j);
- normalized aggregate violation: V_CB(x_i) = sum_j w_j v_{i,j}/s_j^scale.

The deterministic ranking is lexicographic: (1) QUBO/structural feasibility, (2) conservative physical feasibility, (3) aggregate physical violation, (4) QUBO energy, (5) deterministic input-order tie-break. The exact implementation and input contract are authoritative; this document does not silently change source-code semantics.

Statistical limitation: a user-selected z multiplier does not automatically make these intervals calibrated confidence intervals. Unless coverage/calibration is established, call them operational uncertainty bounds or heuristic screening bounds, not certified confidence bounds.

## 3. Frozen C5G7 candidate set and current evidence

Candidate set: MMUU, MUMU, MUUM, UMMU, UMUM, UUMM, with exactly two MOX and two UO2 assemblies; five reflector positions remain invariant. Physical evidence currently available: six layouts × three seed rounds = 18 high-budget OpenMC runs from GitHub Actions run 38229045726 (7,000 batches, 500 inactive, 10,000 particles/batch).

| Layout | Mean k-effective | Mean relative assembly fission-rate peaking proxy |
|---|---:|---:|
| MMUU | 1.1436721 | 1.2953689 |
| MUMU | 1.1437002 | 1.2963641 |
| MUUM | 1.1562627 | 1.3161492 |
| UMMU | 1.1864986 | 1.8671004 |
| UMUM | 1.2046883 | 1.8167198 |
| UUMM | 1.2046416 | 1.8160915 |

The proxy is max(four fuel-assembly integrated fission tallies)/mean(four fuel-assembly integrated fission tallies). It is not absolute power, a licensed safety metric, or by itself a complete physical objective. Lower values mean lower relative assembly-integrated fission-rate peaking under this specific definition only.

Raw-statepoint reconstruction agrees with the exported proxy to max absolute difference 2.22e-16. This is extraction/arithmetic consistency, not independent validation of geometry, nuclear data, tally semantics, or convergence.

## 4. Frozen comparison arms

### Arm A — composition-only QUBO
Objective A*(sum(y_i)-2)^2. For this fixed set, all six candidates have two MOX, so the objective ties all six. Baseline policy: report the full tie set; if a single choice is required for evaluation, use a seed-independent, preregistered uniform random tie-break and repeat over declared randomization seeds. Do not choose the tie-break after seeing physical outcomes.

### Arm B — point-estimate physical ranking
Rank candidates on the declared point estimate of the primary proxy only, without CB-PFR uncertainty-bound screening. This isolates the incremental effect of the CB-PFR uncertainty/feasibility layer. Same candidate information, physical budget, and training/confirmation split as Arm C.

### Arm C — CB-PFR
Use the frozen implementation and predeclared metric bounds, uncertainty estimators, weights, scale values, feasibility priority, and tie policy. No weight, bound, scale, endpoint, or tie-policy tuning on confirmation data.

### Optional Arm D — genuine pre-physics optimizer
Include only if its objective can actually distinguish/rank candidates before OpenMC and it has a documented, fair mapping to the same candidate set. Do not label the composition-only QUBO as a meaningful physical optimizer when all six energies tie.

## 5. Outcomes and statistical reporting

Primary method outcome for a declared synthetic feasibility benchmark: true-feasibility selection rate under the benchmark's data-generating process, with paired method differences and uncertainty intervals over the same trials/pools. Report the preregistered practical-effect threshold unchanged. A failed threshold remains failed; do not replace it post hoc.

For C5G7 physical screening, report separately:
1. per-layout mean and within-run Monte Carlo uncertainty for each declared endpoint;
2. between-seed variability and interval, preserving seed-round pairing where applicable;
3. relative fission-rate peaking proxy;
4. selection consistency across seed rounds;
5. regret against the best observed candidate on the proxy, clearly labelled descriptive/oracle regret;
6. number of failed, invalid, or inconclusive runs and compute budget;
7. convergence and benchmark/model review status.

Do not pool Monte Carlo standard errors and between-seed variation as if they were the same uncertainty source. Do not interpret higher/lower k-effective as automatically better; the intended physical state and acceptance conditions determine admissibility. Do not claim statistical superiority from three seed rounds.

## 6. Leakage control and confirmation protocol

Before confirmation results are opened:
1. Freeze this document, code commit, candidate set, model and MGXS hashes, OpenMC version/settings, primary endpoint, direction of improvement, CB-PFR weights/bounds/scales, missing-data policy, tie policy, baseline implementations, statistical test/interval, practical-effect threshold, randomization seeds, and compute budget.
2. Use existing seed rounds only for exploratory/training decisions. Collect fresh independent confirmation seed rounds under the same fixed model/settings and equal per-arm physical-evaluation budgets.
3. Do not adjust thresholds or hyperparameters after observing confirmation data. Any changes create a new version and require a new untouched confirmation set.
4. Retain all attempts and failures; report them, not just successful runs.
5. Have an independent reviewer sign off model/material mapping, mesh orientation and assembly aggregation, benchmark applicability, source convergence procedure, and physical acceptance criteria.
6. If physical criteria or model review remain unresolved, output NO_SELECTION / INCONCLUSIVE; do not designate a physical winner.

No numeric physical acceptance thresholds are frozen here because no independently justified limits have been approved. The freeze prevents post-hoc tuning; it does not fabricate thresholds.

## 7. Claim boundary frozen

### Supported claims
- CB-PFR is an uncertainty-aware post-optimization ranking/feasibility method implemented in software.
- The current composition-only QUBO enforces two MOX but cannot rank these six candidates because all have equal composition.
- The 18-run OpenMC screening campaign exists, and exported relative fission-rate proxy values were reproduced from raw statepoints to floating-point precision.
- In the current exploratory three-fold leave-one-seed-round-out proxy analysis, MMUU was selected in all three folds with zero observed proxy regret; this is descriptive evidence only.

### Not supported yet
- CB-PFR is statistically superior to QUBO-only or point-estimate ranking on confirmatory data.
- CB-PFR improves actual reactor safety, absolute power peaking, or a licensed physical objective.
- Full physical validation or convergence certification of the C5G7 model.
- Universal/general superiority, quantum advantage, or quantum-hardware use.

### Synthetic benchmark disclosure
The repository's claim-evidence matrix records that the 40,000-pool confirmatory synthetic test did not meet its predeclared practical-effect threshold (pooled gain +0.4875 percentage points versus a ≥2 percentage-point threshold). This result must remain visible and cannot be overwritten by the earlier exploratory result. It is not physical evidence.

## 8. Freeze and change control

This document freezes the comparison protocol and allowed claim wording as of the stated date. It does not freeze the study as physically validated. Source/code changes affecting ranking, uncertainty calculations, endpoints, candidate mapping, or tie handling require a new protocol version and fresh confirmation data. Editorial clarifications that do not change behavior may be documented without changing results.

## 9. Source records

- High-budget OpenMC run: https://github.com/thenextw4ng/cb-pfr/actions/runs/38229045726
- Raw statepoint audit: reports/CBPFR_RAW_STATEPOINT_AUDIT_2026-10-12.md
- Source/convergence audit: reports/CBPFR_PRIMARY_SOURCE_AND_CONVERGENCE_AUDIT_2026-10-12.md
- Full trace diagnostics: reports/CBPFR_C5G7_FULL_TRACE_DIAGNOSTICS_2026-10-12.md
- Direct CB-PFR vs QUBO-only comparison: reports/CBPFR_VS_QUBO_ONLY_DIRECT_COMPARISON_2026-10-12.md
- Claim-to-evidence matrix: reports/EUREKA_CLAIM_EVIDENCE_MATRIX_2026-10-11.md
