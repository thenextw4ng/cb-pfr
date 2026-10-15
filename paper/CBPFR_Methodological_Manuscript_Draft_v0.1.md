# CB-PFR: Evidence-Bounded Screening of QUBO Fuel-Layout Candidates with OpenMC

**Manuscript status:** Revised working draft; scientific claims bounded to the evidence reviewed; software-release audit remains pending.  
**Version:** 0.2, 2026-10-15  
**Study type:** Methodological software paper with an exploratory six-layout C5G7/OpenMC case study.  

## Abstract

Mathematical optimization of nuclear-fuel layouts can satisfy encoded constraints without establishing that a candidate is physically acceptable or that its ranking is robust to simulation uncertainty. This paper proposes and implements CB-PFR, a post-optimization screening and ranking method developed in this work that separates structural feasibility, physical-metric assessment, operational uncertainty bounds, and deterministic candidate ordering. The implementation is designed to make decision rules explicit and to fail closed when required physical evidence is missing or invalid. We demonstrate the framework in a fixed C5G7/OpenMC assembly-placement study with four fuel positions, exactly two MOX and two UO₂ assemblies, and five invariant reflector positions, yielding six feasible arrangements. The composition-only QUBO penalty assigns identical energy to all six feasible arrangements and therefore cannot rank their physical behavior. For the canonical UMMU screening case, the archived high-budget runs give a mean effective multiplication factor of 1.1864932, with a between-seed sample standard deviation of 0.0001557; the mean differs from the saved scalar reference of 1.18655 by −5.679 pcm (combined-uncertainty z-score −0.434). A normalized assembly-distribution comparison reports a maximum absolute relative difference of 0.179% for the reviewed case. Because normalization induces dependence among fractions, this difference is treated as a descriptive consistency check rather than a formal statistical validation test. An archived six-layout campaign contains 18 completed runs across three seed rounds, and its run table is internally cross-checked against case-result records. These results support a bounded numerical-screening and normalized-distribution comparison for the reviewed benchmark case, not complete physical validation. Source-convergence interpretation, independent model-fidelity sign-off, and a prospectively approved physical decision rule remain open. CB-PFR is therefore presented as an auditable screening framework and software contribution; its superiority over alternative decision rules is not established.

**Keywords:** C5G7; fuel management; OpenMC; QUBO; reproducible scientific software

## 1. Introduction

Fuel-layout optimization is a constrained decision problem: an optimizer searches a representation of candidate arrangements, while the physical meaning of its objective depends on the mapping between decision variables, material assignments, geometry, and reactor-physics quantities. A low objective value is only as meaningful as the objective and constraints encoded in the model. In particular, a composition constraint can ensure the required number of assemblies of each material while leaving all feasible permutations indistinguishable.

QUBO is a general binary-quadratic formulation for discrete optimization [1], and quantum or quantum-inspired methods have been investigated for in-core fuel management, including the formulation described by Usmanov et al. [2]. This study uses that research direction as background rather than claiming a direct reproduction of the Usmanov formulation. The present design space is a small, explicitly enumerated C5G7 assembly-placement case: four fuel positions contain two MOX and two UO₂ assemblies, while five reflector positions are held fixed. The six unique fuel assignments are MMUU, MUMU, MUUM, UMMU, UMUM, and UUMM.

A second issue is that candidate assessment may combine different forms of evidence: hard structural constraints, Monte Carlo estimates, operational acceptance limits, and uncertainty summaries. If these are combined without a transparent rule, the resulting ranking can hide missing data, conflate sampling uncertainty with model error, or imply a level of confidence not supported by calibration. CB-PFR is intended to make these steps explicit after candidate generation rather than replace the optimizer or a reactor-physics solver.

The methodological contribution claimed here is the formulation and implementation of this integrated post-optimization decision procedure, not priority over every previously published screening or ranking method. This paper makes three bounded contributions:

1. It proposes and implements CB-PFR as a reproducible post-optimization candidate-screening and ranking method with explicit metric limits, operational uncertainty semantics, violation scoring, and deterministic tie-breaking.
2. It establishes an algebraic limitation of the composition-only QUBO used in the fixed six-layout case: every feasible arrangement receives the same energy, so the objective cannot rank physical performance.
3. It reports an evidence-bounded C5G7/OpenMC case study, including archived run-integrity checks, a canonical scalar numerical screen, and a normalized assembly-distribution comparison, while separating these checks from full physical validation.

The paper does not claim quantum advantage, a validated reactor-safety method, an absolute-power prediction, a physically optimal layout, or statistical superiority of CB-PFR.

## 2. Related Work and Methodological Rationale

Quadratic unconstrained binary optimization (QUBO) is a general formulation for discrete optimization, but the behavior of a solution is determined by the terms encoded in its objective. Kochenberger et al. survey the broader unconstrained binary quadratic programming problem and its solution approaches [1]. In nuclear fuel management, Usmanov et al. formulate an in-core reloading problem using fresh, once-burned, and twice-burned fuel states and compare classical, quantum-inspired, and quantum-annealing methods [2]. This paper draws on that research direction without reproducing its burnup-state encoding or making a quantum-performance claim. Its four-position composition-only QUBO is a deliberately limited baseline.

OpenMC is a Monte Carlo particle-transport code that supports eigenvalue calculations and tally-based analysis [3]. The OECD Nuclear Energy Agency's C5G7 MOX specification defines a multigroup benchmark for heterogeneous UO₂/MOX transport calculations [4]. Song et al. report a two-dimensional C5G7 comparison using a deterministic method-of-characteristics solver with two-level coarse-mesh finite-difference acceleration; their endpoints include effective multiplication factor and assembly/pin power metrics [5]. These works provide code and benchmark context, not a direct baseline for CB-PFR. A reference comparison on one canonical case cannot establish fidelity for every altered layout or qualify a tally-derived proxy as a safety metric.

Uncertainty interpretation and stochastic candidate selection have established literatures. NIST guidance distinguishes uncertainty components and describes how combined or expanded uncertainty depends on stated assumptions [6]. Kim and Nelson survey statistical ranking-and-selection procedures for choosing among stochastic alternatives under specified assumptions [7]. CB-PFR is not presented as a replacement for such statistically designed procedures: its bounds are caller-defined operational screening quantities, not automatically calibrated confidence intervals. The contribution examined here is an auditable post-optimization decision layer that exposes structural checks, metric limits, missing-evidence behavior, violation scoring, and deterministic ordering. This study does not establish improved selection probability or superiority over a formal ranking-and-selection procedure.

## 3. Framework and methods

### 3.1 Study scope and design space

The design space is frozen to six arrangements of four fuel positions. Each arrangement contains exactly two MOX and two UO₂ assemblies. Five reflector positions remain invariant. The candidates are enumerated exhaustively, so there are no unreported feasible permutations within this stated design space. This is an assembly-placement demonstration, not a full-core fuel-management optimization and not a direct reproduction of the fresh/once-burned/twice-burned state encoding in Usmanov et al. [2].

The neutron-transport model is based on the C5G7 benchmark family and the pinned MIT Computational Reactor Physics Group benchmark source at commit `ba41bee54320ada0b4ac39a0dd2ca3c1d090a450`, using OpenMC 0.16.0 and a seven-group structure. The archived high-budget campaign records 7,000 total batches, 500 inactive batches, and 10,000 particles per batch. The canonical scalar confirmation used three seeds (720000, 730000, 740000); the broader six-layout archived campaign covers three seed rounds and 18 runs. Run settings and model/data hashes are retained in the repository evidence package.

### 3.2 Composition-only QUBO and its limitation

Let yᵢ ∈ {0,1} indicate the material category at fuel position i, with yᵢ = 1 representing MOX and yᵢ = 0 representing UO₂. The composition-only penalty is

E(y) = A(Σᵢ yᵢ − 2)², with A > 0.

Every feasible candidate has Σᵢ yᵢ = 2, so E(y) = 0 for all six feasible arrangements. Consequently, this QUBO encodes the composition constraint but contains no discriminating physical term among feasible layouts. This is a property of this objective, not of QUBO optimization in general. The repository includes exhaustive algebraic regression tests for the encoded energy and feasibility behavior.

### 3.3 CB-PFR post-optimization screening

CB-PFR is defined as a post-optimization feasibility and ranking layer. For candidate i and physical metric j, the implementation accepts a supplied estimate μ̂ᵢⱼ, an uncertainty descriptor ŝᵢⱼ, declared lower and/or upper acceptance limits, a nonnegative multiplier zⱼ, a positive scale sⱼ, and a nonnegative weight wⱼ. The operational bounds are

B⁻ᵢⱼ = μ̂ᵢⱼ − zⱼŝᵢⱼ,  B⁺ᵢⱼ = μ̂ᵢⱼ + zⱼŝᵢⱼ.

For lower limit Lⱼ and upper limit Uⱼ, the violation is

vᵢⱼ = max(0, Lⱼ − B⁻ᵢⱼ) + max(0, B⁺ᵢⱼ − Uⱼ),

omitting the term for a limit that is not specified. The normalized aggregate violation is

V_CB(xᵢ) = Σⱼ wⱼvᵢⱼ / sⱼ.

The implementation uses a deterministic lexicographic ranking: (1) structural/QUBO feasibility, (2) conservative physical-feasibility status under the supplied rule, (3) aggregate normalized physical violation, (4) QUBO energy, and (5) stable input order as a final tie-break. Missing or invalid metric inputs are represented explicitly rather than silently treated as passes.

The bound terminology is deliberately conservative. A user-specified multiplier does not by itself provide calibrated confidence coverage, and Monte Carlo sampling uncertainty does not include model-form bias, nuclear-data uncertainty, or geometry/material specification error. Unless a separate calibration argument is supplied, the bounds are operational screening bounds, not certified confidence intervals or safety margins. The method's outcome depends on the metric definitions, limits, uncertainty semantics, scales, and weights declared by the user.

### 3.4 OpenMC outputs and reported metrics

The canonical scalar quantity is the effective multiplication factor, k-effective. Spatial comparison uses normalized assembly-integrated fission-rate fractions against the cited reference fractions for the reviewed benchmark case. Separately, the six-layout exploratory campaign reports a relative assembly-integrated fission-rate peaking proxy defined as the maximum of four fuel-assembly integrated fission tallies divided by their mean:

P_rel = max(F₁, F₂, F₃, F₄) / mean(F₁, F₂, F₃, F₄).

P_rel is a relative tally-derived proxy. It is not absolute power, a pinwise power distribution, a licensed safety metric, or a complete physical objective. The scalar benchmark comparison and normalized spatial-distribution comparison are reported as separate checks because agreement in one does not imply agreement in the other.

### 3.5 Evidence and reproducibility protocol

The archived evidence package includes model/run provenance, per-run hashes, statepoints, tallies, logs, settings, and a run-level table. The high-budget archive was checksum-verified and its 18 embedded run-table rows were cross-checked against 18 case-result records. The recorded campaign has distinct seed and statepoint hashes and a common recorded MGXS hash. Reconstruction of the exported P_rel values agrees with the saved values to a maximum absolute difference of 2.22 × 10⁻¹⁶. These are reproducibility and extraction-integrity checks, not standalone physical validation.

The repository's automated tests and continuous integration pass on Python 3.10, 3.11, and 3.12 for the recorded closeout commit. CI establishes tested software behavior in those environments; it does not certify reactor physics. Source/eigenvalue trace diagnostics were generated from saved batches, but their interpretation remains diagnostic rather than a predeclared convergence certification.

## 4. Results

### 4.1 Algebraic QUBO result

Exhaustive enumeration confirms six unique assignments with the required two-MOX/two-UO₂ composition. For every feasible assignment, the composition-only objective equals zero. Therefore, no physical ordering can be inferred from this objective. A selection policy that returns one candidate from this tie set must declare its tie-breaking rule independently of the observed physical outcomes.

### 4.2 Canonical scalar numerical screen

For the canonical UMMU confirmation, the official repository aggregator reported a mean k-effective of 1.1864932118 and a between-seed sample standard deviation of 0.000155684. The pooled within-run reported standard deviation was 0.000095788. Relative to the saved scalar reference of 1.18655, the difference was −5.679 pcm, with a combined-uncertainty z-score of −0.434. The maximum individual-run reported standard deviation was 9.698 pcm.

These values pass the project's provisional internal numerical-screen criteria: three replicates, unique statepoints, common settings and MGXS/group structure, absolute reference difference no greater than 100 pcm, absolute z-score no greater than 2, and maximum per-run reported standard deviation no greater than 10 pcm. These are project screening criteria, not official OECD/NEA acceptance limits. The scalar result is a numerical screen, not sufficient evidence for full model validation or convergence certification.

### 4.3 Normalized assembly-distribution comparison

For the reviewed canonical benchmark case, the normalized assembly-distribution comparison reported a maximum absolute relative difference of 0.179% against the cited reference fractions, within the corresponding published relative uncertainties. This supports a normalized assembly-distribution comparison for the specific reviewed case. It does not validate absolute watts, flux, pinwise power, all six layouts, or reactor safety. The independent comparison is kept distinct from the machine-generated convergence status because the latter does not itself perform the post-aggregation reference comparison.

### 4.4 Six-layout exploratory campaign and archive integrity

The archived high-budget campaign contains 18 completed recorded runs across six layouts and three seed rounds. The embedded run-level table and case-result records agree on round/layout, candidate identifier, seed, statepoint hash, MGXS hash, and reported k-effective mean and standard deviation. The archive records 18 unique seeds and statepoint hashes, a common MGXS hash, and common settings of 7,000 batches, 500 inactive batches, 10,000 particles per batch, and two threads. The relative peaking proxy reconstruction matches the exported values to floating-point precision.

For the exploratory proxy table, the reported layout means are:

| Layout | Mean k-effective | Mean relative fission-rate peaking proxy |
|---|---:|---:|
| MMUU | 1.1436721 | 1.2953689 |
| MUMU | 1.1437002 | 1.2963641 |
| MUUM | 1.1562627 | 1.3161492 |
| UMMU | 1.1864986 | 1.8671004 |
| UMUM | 1.2046883 | 1.8167198 |
| UUMM | 1.2046416 | 1.8160915 |

MMUU has the lowest mean of this relative proxy in these recorded runs. A descriptive leave-one-seed-round-out procedure selected MMUU in all three folds with zero observed held-out regret for this proxy. Because there are only three seed rounds and the folds reuse the same small set of rounds, this is exploratory consistency evidence rather than prospective independent confirmation. The proxy is not an approved physical acceptance criterion, and this result does not establish MMUU as a physically optimal layout or CB-PFR superiority.

### 4.5 Method-comparison result and negative evidence

A separate synthetic confirmatory benchmark did not meet its preregistered practical-effect threshold: the reported pooled gain was +0.4875 percentage points, below the required minimum of 2 percentage points. This negative result is retained. It prevents a claim that CB-PFR superiority has already been demonstrated, even if the framework is operationally implemented and the C5G7 proxy analysis is descriptively consistent.

The current comparison-readiness audit remains `BLOCKED_NOT_IDENTIFIABLE` because a comparable pre-physics QUBO score table and an approved, predeclared physical acceptance-rule file are absent from the comparison inputs. Independent primary-model/tally sign-off and prospective confirmation also remain open.

## 5. Discussion

The equal-energy result is an exact consequence of the composition-only QUBO, not evidence that QUBO is unsuitable for fuel-layout problems generally. Because every feasible state contains exactly two MOX assemblies, the penalty has no term that distinguishes spatial arrangements. In this six-layout design space, the objective enforces material inventory but cannot rank the candidates by neutron-transport response. A physics-informed objective could add such distinctions, but its terms, scaling, and interaction with constraints would require separate justification and verification.

The six-layout OpenMC campaign shows that the recorded model produces different responses for different layouts. MMUU has the lowest three-run mean of the relative assembly-integrated fission-rate peaking proxy, while UMMU has the highest. This ordering is descriptive only: there are three seed rounds per layout, no independently approved physical acceptance band, and the proxy is not absolute power or a qualified safety endpoint. The result therefore demonstrates the distinction between the encoded objective and the simulated response, not a physically optimal layout.

For the separate canonical UMMU screen, the mean effective multiplication factor differed from the saved scalar reference by −5.679 pcm; the audit reports a combined-uncertainty z-score of −0.434 under its stated uncertainty interpretation. The normalized assembly-distribution comparison had a maximum absolute relative difference of 0.179%. These are useful numerical checks for one reviewed case, but they do not amount to a formal coverage or equivalence test. Published uncertainties for unnormalized assembly powers cannot automatically be interpreted as the uncertainty of normalized, dependent fractions. Neither comparison establishes source convergence or validates all six altered layouts.

The methodological contribution is an inspectable post-optimization procedure that separates structural feasibility, physical-metric estimates, operational bounds, normalized violation scoring, missing-evidence behavior, and deterministic ordering. The 18-run archive's seed, statepoint, MGXS, settings, record-agreement, and tally-extraction checks support internal provenance and arithmetic consistency; the reconstructed proxy agreed with the exported values to a maximum absolute difference of 2.22 × 10⁻¹⁶. Such checks are necessary for reproducible software but cannot establish the correctness of the upstream physical model.

No incremental CB-PFR selection gain was demonstrated. A fixed-budget exploratory ranking-and-selection comparison selected the same layout for CB-PFR and the baseline. Separately, the synthetic confirmatory benchmark's gain of +0.4875 percentage points fell below its prespecified threshold of at least 2 percentage points. These are distinct comparisons and should not be conflated with a physical validation experiment. The evidence supports saying that superiority has not been demonstrated; it does not establish that CB-PFR is inferior in every setting. No quantum-processing-unit execution or quantum advantage is claimed.

## 6. Limitations and Evidence Needed

This study covers only six arrangements of four variable fuel positions with five reflector positions fixed; it does not establish scalability to realistic full-core fuel-management problems. Three seed rounds limit the stability of layout-level summaries. The model is a two-dimensional, multigroup C5G7-derived calculation, and independent sign-off of model fidelity and source-convergence interpretation remains outstanding. The spatial metric is an assembly-integrated fission tally used as a relative proxy, not absolute power, pin-wise power, thermal-hydraulic performance, burnup behavior, or a safety criterion. The canonical three-seed scalar screen and the 18-run layout archive are separate campaigns and must not be pooled. Reference comparisons are restricted to one reviewed case. Finally, CB-PFR's operational bounds depend on user-declared limits and uncertainty descriptors; calibrated coverage and comparative selection performance have not been established.

A stronger follow-up requires: (1) independent review of geometry, material mapping, nuclear data, tally definitions, and correspondence to the C5G7 specification; (2) documented source-convergence and eigenvalue diagnostics, including batch/generation histories and repeatability under independent seeds; (3) physical acceptance criteria justified for the intended analysis and fixed before candidate evaluation; (4) an uncertainty treatment that distinguishes Monte Carlo sampling uncertainty from reference, nuclear-data, and model-form uncertainty; and (5) a prospective equal-budget comparison against suitable baselines over multiple cases, using prespecified outcomes and a statistically justified decision rule. Claims of generality would additionally require larger and structurally different candidate spaces. Until these conditions are met, the work should be read as a bounded methodological and research-software demonstration, not complete physical validation or an engineering recommendation.

## 7. Conclusion

This work proposes and implements CB-PFR as an auditable post-optimization screening and ranking method. In the fixed C5G7/OpenMC case, the composition-only QUBO assigns zero energy to all six layouts containing two MOX and two UO₂ assemblies, so the objective enforces composition but cannot rank their physical responses. The 18-run archive passed the reported internal provenance and tally-extraction checks. For a separate canonical UMMU screen, the mean effective multiplication factor was −5.679 pcm relative to the saved scalar reference, and the single-case normalized assembly-distribution comparison had a maximum absolute relative difference of 0.179%. These findings are numerical consistency checks, not general validation.

The current evidence establishes an implemented decision procedure, not a physically optimal layout, calibrated confidence guarantees, full physical validation, or superiority over a comparable selection method. The next evidentiary step is independent model-fidelity and convergence review, followed by prospectively justified physical criteria and a fair confirmatory comparison.

## 8. Data and code availability

Code, tests, protocol specifications, evidence reports, and the archived-run audit tools are maintained in the CB-PFR repository: https://github.com/thenextw4ng/cb-pfr. The paper's final version should identify the exact release commit, archive DOI or durable artifact identifier, and the hashes of all analyzed inputs before submission. The raw high-budget archive checksum recorded in the current closeout is `be48b17c2c336a97d08673d191457b9c695853759180116f5382f636b4c93019`.

## 9. References

[1] G. Kochenberger, J.-K. Hao, F. Glover, M. Lewis, Z. Lü, H. Wang, and Y. Wang, “The unconstrained binary quadratic programming problem: A survey,” *Journal of Combinatorial Optimization*, vol. 28, no. 1, pp. 58–81, 2014. https://doi.org/10.1007/s10878-014-9734-0.

[2] S. R. Usmanov, G. V. Salakhov, A. A. Bozhedarov, E. O. Kiktenko, and A. K. Fedorov, “Quantum and quantum-inspired optimization for an in-core fuel management problem,” *Journal of Physics: Conference Series*, vol. 2701, no. 1, Art. no. 012031, 2024. https://doi.org/10.1088/1742-6596/2701/1/012031.

[3] P. K. Romano, N. E. Horelik, B. R. Herman, A. G. Nelson, B. Forget, and K. Smith, “OpenMC: A state-of-the-art Monte Carlo code for research and development,” *Annals of Nuclear Energy*, vol. 82, pp. 90–97, 2015. https://doi.org/10.1016/j.anucene.2014.07.048.

[4] E. E. Lewis, M. A. Smith, N. Tsoulfanidis, G. Palmiotti, T. A. Taiwo, and R. N. Blomquist, *Benchmark Specification for Deterministic 2-D/3-D MOX Fuel Assembly Transport Calculations without Spatial Homogenisation (C5G7 MOX)*, OECD Nuclear Energy Agency, Tech. Rep. NEA/NSC/DOC(2001)4, 2001. https://www.oecd-nea.org/science/wprs/eg3drtb/NEA-C5G7MOX.PDF.

[5] P. Song, Q. Zhang, L. Liang, Z. Zhang, and Q. Zhao, “GPU-based two-level CMFD accelerating two-dimensional MOC neutron transport calculation,” *Frontiers in Energy Research*, vol. 8, Art. no. 124, 2020. https://doi.org/10.3389/fenrg.2020.00124.

[6] B. N. Taylor and C. E. Kuyatt, *Guidelines for Evaluating and Expressing the Uncertainty of NIST Measurement Results*, NIST Technical Note 1297, National Institute of Standards and Technology, 1994. https://doi.org/10.6028/NIST.tn.1297.

[7] S.-H. Kim and B. L. Nelson, “Selecting the best system,” in *Simulation*, Handbooks in Operations Research and Management Science, vol. 13, pp. 501–534, Elsevier, 2006. https://doi.org/10.1016/S0927-0507(06)13017-0.

## Author checklist before submission

- [ ] Confirm author list, affiliations, corresponding author, and funding/acknowledgements.
- [ ] Add a methods figure showing candidate generation → structural check → OpenMC assessment → CB-PFR screening/ranking → evidence report.
- [ ] Verify every reported number against the frozen raw tables and save the analysis outputs in the release package.
- [ ] Confirm the exact canonical spatial-reference table, units, and calculation of the 0.179% maximum relative difference.
- [ ] Add uncertainty summaries and appropriate plots without presenting three seed rounds as calibration.
- [ ] Reconcile all reported run settings by campaign (canonical UMMU: one thread; six-layout archive: two threads).
- [x] Verify primary-source metadata for QUBO, OpenMC, C5G7, uncertainty guidance, and statistical ranking-and-selection; prepare compilable BibTeX.
- [ ] Perform the software-release and artifact-hash closeout before claiming an archival release or DOI.
- [ ] Keep the negative synthetic benchmark result and all claim boundaries in the final version.
