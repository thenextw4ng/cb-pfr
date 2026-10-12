# CB-PFR: evidence-bounded scientific claims and manuscript wording

**Prepared:** 2026-10-12  
**Scope:** Current frozen six-layout C5G7/OpenMC study and CB-PFR implementation  
**Purpose:** State what the existing evidence supports without inflating exploratory results into validation or superiority claims.

## 1. Main scientific claim that can be made now

> We implement CB-PFR as a post-optimization candidate-screening and ranking framework that combines structural/QUBO feasibility with explicitly declared operational uncertainty bounds and physical-metric acceptance limits. In the fixed six-layout C5G7 case study, a composition-only QUBO penalty cannot distinguish among feasible layouts because all contain exactly two MOX and two UO2 assemblies. The archived OpenMC campaign provides an internally cross-checked, three-round exploratory comparison of a relative assembly-integrated fission-rate peaking proxy, but it does not establish physical validation or CB-PFR superiority.

This is a legitimate **method/software contribution plus bounded computational case study**. It is not a claim that CB-PFR is a validated reactor-physics method or statistically superior decision rule.

## 2. Specific claims and evidence

### Claim A — A transparent post-optimization decision layer is implemented
**Claim:** CB-PFR separates candidate generation/structural feasibility from downstream physical screening and deterministic ranking. Missing or invalid physical metrics are not silently treated as passing results; the ranking implementation exposes missing/invalid assessment states.

**Evidence to cite:** src/cbpfr/ranking.py, the frozen method specification, regression tests, and CI run recorded in the closeout report.

**Boundary:** This establishes implemented software behavior, not calibrated uncertainty coverage, safety qualification, or predictive validity.

### Claim B — The composition-only QUBO is insufficient to rank physical layouts
**Claim:** For the objective E(y) = A(sum(y_i) - 2)^2, every feasible four-position layout with exactly two MOX assemblies has the same energy. The objective enforces composition but contains no term that distinguishes physical performance among the six feasible permutations.

**Evidence:** Algebraic identity plus exhaustive QUBO regression tests in tests/test_qubo_algebraic_regression.py.

**Boundary:** This is a statement about this particular objective, not about QUBO methods generally. It motivates downstream physical screening; it does not prove CB-PFR superiority.

### Claim C — The archived simulation campaign is internally traceable
**Claim:** The archived campaign contains 18 completed recorded runs (six layouts × three seed rounds), with distinct recorded seeds and statepoint hashes, one recorded MGXS hash, and common recorded run settings. The embedded source table was cross-checked against 18 case-result records. Reconstruction of the exported relative peaking proxy agrees to a maximum absolute difference of 2.22e-16.

**Evidence:** reports/CBPFR_RELEASE_REPRODUCIBILITY_CHECK_2026-10-12.md and the archived raw artifact identified there.

**Boundary:** Internal consistency and arithmetic reconstruction are not independent validation of geometry/material mapping, nuclear data, tally semantics, or source convergence.

### Claim D — An exploratory proxy ranking is observable, but not confirmatory
The frozen run-level summary reports the following mean values:

| Layout | Mean k-effective | Mean relative assembly-integrated fission-rate peaking proxy |
|---|---:|---:|
| MMUU | 1.1436721 | 1.2953689 |
| MUMU | 1.1437002 | 1.2963641 |
| MUUM | 1.1562627 | 1.3161492 |
| UMMU | 1.1864986 | 1.8671004 |
| UMUM | 1.2046883 | 1.8167198 |
| UUMM | 1.2046416 | 1.8160915 |

For this proxy and these recorded runs, MMUU has the lowest mean among the six layouts. The recorded three-fold leave-one-round-out descriptive procedure selected MMUU in all three folds and reported zero observed held-out proxy regret.

**Boundary:** There are only three seed rounds; the folds are not independent prospective confirmation. The proxy is max(four assembly-integrated fission tallies) / mean(four assembly-integrated fission tallies), not absolute power or an approved safety metric. Do not call MMUU a validated physical winner.

### Claim E — Current evidence does not establish CB-PFR superiority
The frozen comparison audit is BLOCKED_NOT_IDENTIFIABLE: a comparable pre-physics QUBO score table and an approved predeclared physical acceptance-rule file are absent from the audit inputs, while independent model/tally review and prospective confirmation remain open. A separate synthetic confirmatory benchmark failed its preregistered practical-effect threshold (reported gain +0.4875 percentage points versus a threshold of at least 2 percentage points).

**Boundary:** Report this negative result. Do not replace it with the exploratory C5G7 ranking or change thresholds after seeing outcomes.

## 3. Recommended title and abstract positioning

**Recommended title:**  
*CB-PFR: An Uncertainty-Aware Post-Optimization Screening Framework for Fuel-Layout Candidates — Implementation and an Exploratory C5G7 Case Study*

**Abstract-ready core paragraph:**  
This study presents CB-PFR, an uncertainty-aware post-optimization screening and ranking framework for evaluating candidate fuel layouts after mathematical optimization. The framework makes structural feasibility, operational uncertainty bounds, physical acceptance limits, and deterministic ranking explicit, while distinguishing software checks from physical validation. In a six-layout C5G7/OpenMC case study with exactly two MOX and two UO2 assemblies per layout, the composition-only QUBO objective assigns equal energy to every feasible arrangement and therefore cannot rank physical outcomes. An archived campaign of 18 runs across three seed rounds was internally cross-checked against case-result records, and reconstruction of the relative assembly-integrated fission-rate peaking proxy matched exported values to floating-point precision. Exploratory leave-one-round-out analysis selected MMUU in all three folds for this proxy, but the small number of rounds and the proxy's limited physical interpretation preclude a confirmatory winner claim. A separate synthetic benchmark did not meet its preregistered practical-effect threshold. Thus, the contribution is a transparent and auditable screening implementation with an exploratory computational demonstration; CB-PFR superiority and full physical validation remain unestablished.

## 4. Required wording discipline

Use: “implemented”, “operational uncertainty bounds”, “exploratory case study”, “relative assembly-integrated fission-rate peaking proxy”, “internal archive consistency”, and “not established”.

Do not use without new appropriate evidence: “validated reactor-safety method”, “absolute power peaking”, “physically optimal layout”, “CB-PFR outperforms baseline”, “certified confidence bounds”, “quantum advantage”, or “real-reactor validation”.

## 5. What would change the strength of the claim

A stronger physical-performance claim requires, at minimum:
1. Independent review/sign-off of geometry, material mapping, and tally interpretation.
2. A documented source-convergence review for the relevant layouts and metrics.
3. A physically justified acceptance rule frozen before evaluating confirmation outcomes.
4. Prospective independent confirmation rounds and a fair, predeclared baseline comparison.
5. A reproducible final-checkout run with its logs, JSON audit outputs, and artifact checksums retained.

Do not rerun the expensive OpenMC campaign merely to improve the wording of the current claim. First exhaust the existing raw archive and saved statepoints for evidence that can be audited without rerunning transport.
