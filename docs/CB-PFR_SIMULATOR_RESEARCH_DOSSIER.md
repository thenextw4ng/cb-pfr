# CB-PFR Simulator — consolidated research dossier

**Project name:** CB-PFR Simulator  
**Method name:** CB-PFR (Confidence-Bounded Physical Feasibility Ranking)  
**Evidence snapshot:** 12 October 2026  
**Status:** Consolidated research record; not a validation certificate  
**Study class:** Research software and methodological case study

## 1. Executive summary

CB-PFR Simulator is research software intended to connect three tasks: (1) generate or enumerate candidate fuel layouts using a discrete optimization formulation such as QUBO; (2) evaluate candidates with physics-based neutron-transport calculations in OpenMC; and (3) apply CB-PFR as an explicit post-optimization screening/ranking layer that considers declared physical metrics, uncertainty summaries, and decision rules.

The scientific problem is the gap between **mathematical feasibility under an encoded objective** and **evidence-based selection after physical simulation**. A QUBO solver can return a low-energy state without establishing that its physical interpretation is adequate, that the candidate meets an independently justified physical criterion, or that apparent differences exceed simulation uncertainty. CB-PFR makes the post-optimization decision stage explicit and auditable.

The repository contains a CB-PFR ranking implementation, algebraic QUBO tests, synthetic benchmark code and records, C5G7/OpenMC layout-study tooling, run-archive audits, reproducibility reports, and automated CI. The evidence supports a research-software/methodological contribution and an exploratory case study. It does **not** establish full physical validation, a certified physically optimal layout, confirmatory CB-PFR superiority, or quantum-hardware advantage.

## 2. Research question and objectives

### Main research question

How can QUBO-based candidate generation be connected to physics-based neutron-transport evaluation and uncertainty-aware post-optimization screening so that candidate selection is traceable to declared physical criteria rather than relying on the optimizer's objective value alone?

### Objectives

1. Represent discrete fuel-layout constraints and enumerate the feasible candidate set.
2. Evaluate candidates with a consistent OpenMC model and preserve input, data, seed, statepoint, and tally provenance.
3. Distinguish structural feasibility, simulated physical response, sampling uncertainty, and decision rules.
4. Apply CB-PFR as a post-optimization feasibility/ranking layer with explicit bounds, violation scoring, and deterministic tie-breaking.
5. Audit reproducibility and ensure every scientific claim is limited to its supporting evidence.
6. Provide a foundation for later studies with justified physical acceptance criteria, prospective confirmation, and fair optimization baselines.

## 3. What the software does

Workflow: **candidate encoding / QUBO → feasible-layout enumeration or optimization → OpenMC neutron-transport simulation → tally extraction and uncertainty summary → CB-PFR screening/ranking → auditable candidate report.**

- **QUBO / discrete optimization:** encodes a combinatorial search problem. QUBO is a mathematical formulation; it may be solved classically, heuristically, or with quantum annealing hardware.
- **OpenMC:** estimates neutron-transport quantities from geometry, materials, nuclear data, source settings, and tallies.
- **CB-PFR:** assesses candidates after optimization, using declared physical-metric bounds and uncertainty information. Its operational bounds are not automatically calibrated confidence intervals or safety margins.
- **Evidence/audit layer:** retains provenance and checks consistency of data extraction, run coverage, hashes, settings, and claim-to-evidence alignment.

CB-PFR is not itself a neutron-transport solver, not a QUBO optimizer, and not a reactor-safety certification tool.

## 4. Physical model and candidate space

The focused C5G7 assembly-placement study fixes five reflector positions and varies four fuel positions. Each fuel position is assigned either MOX or UO₂, with exactly two of each. The exhaustive feasible set contains six arrangements:

| Layout | Four fuel-position labels |
|---|---|
| MMUU | MOX, MOX, UO₂, UO₂ |
| MUMU | MOX, UO₂, MOX, UO₂ |
| MUUM | MOX, UO₂, UO₂, MOX |
| UMMU | UO₂, MOX, MOX, UO₂ |
| UMUM | UO₂, MOX, UO₂, MOX |
| UUMM | UO₂, UO₂, MOX, MOX |

The study uses a pinned upstream C5G7 benchmark source at commit ba41bee54320ada0b4ac39a0dd2ca3c1d090a450, OpenMC 0.16.0 for the corrected-group layout campaign, and the standard seven-group boundaries recorded in the repository. These four-position layouts are a bounded assembly-placement case study, not a full-core fuel-management optimization and not a direct reproduction of the burnup-state encoding in Usmanov et al.

### Physical quantities used

- **Effective multiplication factor, k-effective:** neutron-multiplication indicator estimated by the eigenvalue calculation.
- **Assembly-integrated fission tally:** integrated fission reaction score for each of the four fuel regions.
- **Relative assembly-integrated fission-rate peaking proxy:**

F = max(R₁, R₂, R₃, R₄) / mean(R₁, R₂, R₃, R₄),

where Rᵢ is the assembly-integrated fission tally for fuel region i. This is dimensionless and relative. It is **not** absolute power in watts, pinwise power, a thermal-hydraulic quantity, or a reactor-safety limit.

## 5. QUBO formulation and what it proves

For four binary material indicators yᵢ ∈ {0,1}, where 1 denotes MOX and 0 denotes UO₂, the composition-only penalty is

E(y) = A (Σᵢ yᵢ − 2)², with A > 0.

It penalizes assignments that do not contain exactly two MOX assemblies. For every feasible layout, the sum is 2 and the penalty is zero. Therefore, **all six feasible layouts tie under this objective**.

This is an algebraic limitation of the particular composition-only objective, not of QUBO in general. The current objective encodes composition; it does not encode physical performance and cannot by itself select the layout with the best neutron-physics response. The repository includes exhaustive enumeration and regression checks for this property.

The older QUBO formulation using fresh / once-burned / twice-burned categorical states is a separate model. The repository explicitly records that no defensible mapping from that legacy state encoding to the current C5G7 UO₂/MOX layout has been established. The two formulations must not be conflated.

## 6. CB-PFR method

For candidate i and metric j, the implementation computes operational bounds from an estimate and an uncertainty summary:

B⁻ᵢⱼ = μ̂ᵢⱼ − zⱼ ŝᵢⱼ  
B⁺ᵢⱼ = μ̂ᵢⱼ + zⱼ ŝᵢⱼ

For declared acceptable limits Lⱼ and Uⱼ, the interval violation is

vᵢⱼ = max(0, Lⱼ − B⁻ᵢⱼ) + max(0, B⁺ᵢⱼ − Uⱼ).

The aggregate normalized violation is

V_CB(xᵢ) = Σⱼ wⱼ vᵢⱼ / sⱼ(scale).

The implementation uses deterministic ordering that prioritizes structural/QUBO feasibility, conservative physical feasibility, aggregate violation, QUBO energy, and a stable tie-break. Missing or invalid evidence should not silently be treated as a passing physical assessment.

**Statistical interpretation:** the multiplier zⱼ is an operational parameter unless its statistical calibration and assumptions are justified. The resulting bounds must not automatically be called calibrated confidence intervals, predictive guarantees, or safety margins. Monte Carlo sampling uncertainty is distinct from model-form, nuclear-data, geometry, material-mapping, and experimental uncertainty.

## 7. Research and implementation history: relevant evidence only

The repository contains a much larger history of experiments. This section separates evidence directly relevant to the focused CB-PFR Simulator story from historical or exploratory branches.

### 7.1 Software and reproducibility

- The CB-PFR implementation, abstract QUBO utilities, tests, examples, evidence audits, and automated workflows are present.
- CI for closeout/manuscript commit 76d084cdfab7b789dd48d70f4793b53f79b4ab82 completed successfully in [workflow run 38270407515](https://github.com/thenextw4ng/cb-pfr/actions/runs/38270407515).
- The high-budget archive recorded in the closeout report has SHA-256 be48b17c2c336a97d08673d191457b9c695853759180116f5382f636b4c93019, 565 ZIP entries, 18 run-level records, 18 distinct recorded seeds/statepoint hashes, and one common recorded MGXS hash. The embedded run-level table was cross-checked against 18 case-result records.
- Reconstructing the exported relative fission-rate peaking proxy from the saved tally was reported to match with maximum absolute discrepancy 2.22 × 10⁻¹⁶. This demonstrates arithmetic/extraction consistency, not independent physical-model validation.

### 7.2 Corrected-group six-layout exploratory study

The corrected-group smoke study recorded 18 runs across six layouts and three seed rounds, with corrected seven-group structure and a common MGXS hash. The documented descriptive table was:

| Layout | Mean k-effective | Mean relative fission-peaking proxy | Between-seed SD of proxy | Descriptive proxy rank |
|---|---:|---:|---:|---:|
| MUMU | 1.14482492 | 1.296265 | 0.022605 | 1 |
| MUUM | 1.15847361 | 1.310279 | 0.022338 | 2 |
| MMUU | 1.14541306 | 1.327285 | 0.011865 | 3 |
| UUMM | 1.20511523 | 1.825391 | 0.024419 | 4 |
| UMUM | 1.20789406 | 1.855918 | 0.046896 | 5 |
| UMMU | 1.18610263 | 1.886113 | 0.028995 | 6 |

These values are from the documented smoke-budget campaign (100 batches, 10 inactive, 1,000 particles per batch). They are descriptive only, not benchmark-grade convergence. They show why a single proxy cannot be used alone: MUMU ranks lowest by the proxy, while its mean k-effective is about 1.1448, far from the standard C5G7 reference region. No approved design-specific acceptance band exists, so this table does not designate a winner.

### 7.3 CB-PFR/QUBO integration smoke

A recorded integration workflow consumed the corrected-group 18-run smoke dataset, audited the inputs, enumerated all 2⁶ = 64 one-hot selector states, and selected MUMU under explicitly illustrative limits. All six layouts passed those illustrative screening limits. This establishes that the code path can connect archived OpenMC data, CB-PFR fields, and a one-hot QUBO selection mechanism. It does not establish a benchmark-grade physical winner: the limits were chosen to exercise the integration path, not derived as official C5G7 criteria.

### 7.4 High-budget archived campaign and canonical scalar screen

A separate high-budget archive records 18 runs (six layouts × three rounds) with 7,000 batches, 500 inactive batches, 10,000 particles per batch, two threads, unique recorded seeds/statepoint hashes, and common MGXS provenance. A canonical UMMU scalar screen reports:

| Metric | Recorded result |
|---|---:|
| Mean k-effective | 1.1864932118 |
| Between-seed sample SD | 0.000155684 |
| Pooled within-run reported SD | 0.000095788 |
| Difference from saved scalar reference 1.18655 | −5.679 pcm |
| Combined-uncertainty z-score | −0.434 |
| Maximum individual-run reported SD | 9.698 pcm |

The project's provisional internal numerical-screen criteria passed. These criteria are not official OECD/NEA acceptance limits, and the run summary alone does not certify source convergence or physical fidelity of all six layouts.

A normalized assembly-distribution comparison for the reviewed canonical case reported maximum absolute relative difference of 0.179% against cited reference fractions, within the corresponding stated relative uncertainties. This supports a normalized assembly-distribution comparison for that reviewed case only. It does not validate absolute power, flux, pinwise distributions, the other five altered layouts, or reactor safety.

**Dataset distinction:** the smoke-budget 18-run table and the separate high-budget 18-run archive are distinct campaigns with different budgets and reported summaries. Their values must not be merged into one table or treated as interchangeable replicates. The paper should cite each campaign by its specific artifact/report and explain its purpose.

### 7.5 Synthetic benchmark

The repository includes a reduced synthetic benchmark with 1,000 trials per method (4,000 method/trial rows). Recorded selected true-feasibility rates were QUBO-only 0.857, point estimate 0.933, CB-PFR 0.976, and uniform margin 0.966 under the benchmark's declared data-generating process. These results are conditional on a synthetic setup, not nuclear-physics evidence.

A separate confirmatory synthetic benchmark failed its prespecified practical-effect threshold: pooled gain was +0.4875 percentage points against a required threshold of at least 2 percentage points. That negative result must be disclosed whenever the confirmatory synthetic evaluation is discussed. It prevents a broad confirmatory superiority claim.

A supplementary local QAOA software experiment on a separate synthetic 10-variable cardinality-constrained QUBO is archived in the [local QAOA report](../reports/LOCAL_QAOA_SYNTHETIC_QUBO_EVALUATION_2026-10-16.md), with its [result JSON](../experiments/local_qaoa_synthetic_qubo_20261016/qaoa_local_test_results.json) and [extracted n=10 instance](../experiments/local_qaoa_synthetic_qubo_20261016/n10_problem_instance.json). The Ising mapping passed an exhaustive 1,024-bitstring check and one sampled state reached the synthetic exact optimum, but the parameter optimizer did not terminate successfully. This was a local simulator run, not a QPU job; it does not establish quantum advantage and is not mapped to C5G7/OpenMC fuel layouts. Keep it separate from physical-study results.\n\n### 7.6 BEAVRS comparison attempt

The repository includes a BEAVRS Cycle 1 day-0 detector-map comparison workflow. The executed spatial-map comparison had poor agreement (reported RMSE 0.33426 and correlation −0.0780) and known model/measurement alignment and detector-response uncertainty issues. It is evidence that the comparison workflow executed and revealed a mismatch; it is **not physical-validation evidence** and must not be described as successful validation.

### 7.7 Classical simulated annealing / R&S comparison

The recorded fixed-budget comparison on the same 18-run corrected-group smoke data found that CB-PFR and an equal-allocation fixed-budget ranking-and-selection baseline both selected MUMU. Incremental selection gain was therefore not demonstrated in that comparison. A path-integral annealing experiment found the exact selector minimum in 166/500 reads (33.2%) and returned one-hot samples in 500/500 reads; this was **classical simulated quantum annealing**, not quantum-processing-unit execution.

## 8. What the evidence currently supports

### Supported claims

1. CB-PFR is implemented as an uncertainty-aware post-optimization screening/ranking layer with explicit operational bounds, violation scoring, and deterministic tie-breaking.
2. The current composition-only QUBO enforces the two-MOX composition constraint but cannot rank the six feasible layouts.
3. The repository contains an auditable OpenMC C5G7 layout-study pipeline and archived campaigns with recorded provenance and automated checks.
4. The CB-PFR/QUBO/OpenMC integration path has been exercised on archived candidate data under illustrative screening limits.
5. A normalized assembly-distribution comparison and scalar numerical screen were reported for a reviewed canonical case, with bounded interpretation.
6. The synthetic and C5G7 experiments expose meaningful limitations, including failure to meet the confirmatory synthetic practical-effect threshold and lack of demonstrated incremental gain over a simple baseline in one exploratory comparison.

### Not established

- A physically optimal layout or an approved candidate for reactor engineering.
- Complete C5G7 validation or convergence certification for all six layouts.
- Absolute power, pinwise power, thermal-hydraulic, or reactor-safety validation.
- Confirmatory CB-PFR superiority over QUBO-only, point-estimate, uniform-margin, or R&S baselines on physical data.
- A defensible mapping from the legacy burnup-state QUBO to the UO₂/MOX C5G7 layout.
- Quantum-hardware execution or quantum advantage.
- Generalization to other reactor geometries, fuel-management problems, or operating conditions.

## 9. Why the project is physically meaningful

The physical object is the spatial arrangement of fuel materials in a neutron-transport model. MOX and UO₂ have different nuclear compositions and interaction characteristics; changing their positions changes the material configuration through which neutrons are transported. OpenMC estimates neutron-physics quantities from this configuration, including k-effective and region-integrated fission tallies. CB-PFR then treats those outputs as physical evidence to be evaluated under declared rules.

The project draws on reactor physics and computational neutron transport. It does not solve microscopic nuclear quantum states directly. Quantum enters the optimization framing only when a QUBO is submitted to a quantum-annealing device; QUBO formulation and classical enumeration by themselves are not quantum-hardware execution. Current evidence does not establish quantum advantage.

## 10. Value and intended use for Indonesia

As research software, CB-PFR Simulator can support Indonesian education and research in computational reactor physics, combinatorial optimization, uncertainty-aware engineering decisions, and reproducible scientific computing. It provides a platform to investigate how candidate-generation methods can be connected to physics-based evidence, while preserving traceability of inputs, results, and decision rules.

These are research-capacity and future-development benefits. The current work does not demonstrate operational cost savings, improved reactor safety, readiness for a licensed design decision, or a deployment-ready nuclear engineering product.

## 11. Prioritized next steps

1. **Consolidate public narrative:** use “CB-PFR Simulator” as the software/project name and “CB-PFR” as the screening method name. Link this dossier and the working paper from the repository front page.
2. **Keep data campaigns distinct:** label smoke-budget, high-budget, canonical scalar, synthetic, and BEAVRS results separately in every table and figure.
3. **Finalize the method-to-evidence mapping:** for every simulator output, record its source artifact, formula, units, uncertainty meaning, and allowed interpretation.
4. **Resolve the physical decision rule before any winner claim:** specify an approved k-effective acceptance band and any other physical criteria prospectively; do not tune thresholds after observing rankings.
5. **Review source convergence and model/tally fidelity:** retain existing evidence and request qualified independent review before considering any additional expensive transport runs.
6. **Evaluate fair baselines:** compare CB-PFR with point estimates, fixed margins, and ranking-and-selection under the same candidate data, simulation budgets, and predeclared endpoint.
7. **Improve QUBO objective only as a separate, justified method step:** if adding physical terms, document their mapping, scaling, constraints, and effect on the feasible set. Do not present the current composition-only QUBO as a physical optimizer.
8. **Keep quantum claims precise:** if no QPU job is recorded, describe the system as QUBO-based or quantum-compatible optimization; separately report classical simulated annealing.
9. **Release responsibly:** rerun documented audit commands on the exact release checkout, archive their outputs, pin dependencies, provide a reproducible quick start, and retain limitations in release notes.

## 12. Primary repository artifacts

- [Methodological manuscript draft](../paper/CBPFR_Methodological_Manuscript_Draft_v0.1.md)
- [Evidence-bounded claims](../reports/CBPFR_EVIDENCE_BOUNDED_SCIENTIFIC_CLAIMS_2026-10-12.md)
- [Final package closeout and claim boundary](../reports/CBPFR_FINAL_PACKAGE_CLOSEOUT_2026-10-12.md)
- [A–G final evidence closeout](../reports/CBPFR_A-G_FINAL_EVIDENCE_CLOSEOUT_2026-10-12.md)
- [Claim-to-evidence matrix](../reports/EUREKA_CLAIM_EVIDENCE_MATRIX_2026-10-11.md)
- [C5G7 CB-PFR/QUBO integration smoke](../reports/c5g7_cbpfr_selection_smoke_2026-10-11.md)
- [Corrected-group repeatability smoke report](../reports/c5g7_corrected_group_repeatability_smoke_2026-10-11.md)
- [C5G7 physical mapping and validation plan](../reports/C5G7_VALIDATION_AND_MAPPING_PLAN.md)
- [Fixed-budget R&S and classical SQA comparison](../reports/C5G7_FIXED_BUDGET_RS_SQA_COMPARISON_2026-10-11.md)
- [BEAVRS comparison protocol](../reports/BEAVRS_CYCLE1_EXPERIMENTAL_COMPARISON_PROTOCOL.md)

## 13. Recommended software description

**CB-PFR Simulator is research software for connecting QUBO-based candidate generation, OpenMC neutron-transport evaluation, and uncertainty-aware post-optimization screening of fuel-layout candidates.** It is designed to make candidate-selection rules and evidence provenance explicit. Current results establish an implemented and auditable research workflow with exploratory computational evidence; physical optimality, full benchmark validation, confirmatory superiority, and quantum advantage remain unestablished.
