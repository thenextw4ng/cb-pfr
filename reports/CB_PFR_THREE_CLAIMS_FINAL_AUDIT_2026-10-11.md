# Final audit of the three proposed claims — 11 October 2026

**Repository:** `thenextw4ng/cb-pfr`  
**Scope:** evidence audit of the three requested claims, existing C5G7/OpenMC artifacts, the legacy Usmanov-style QUBO, and quantum-computing evidence.  
**Decision standard:** a claim is marked supported only if the current repository contains evidence that directly supports that wording.

## Executive decision

| Requested claim | Final status | What the current evidence supports |
|---|---|---|
| 1. “CB-PFR terbukti meningkatkan kualitas optimisasi bahan bakar reaktor secara fisik.” | **NOT ESTABLISHED** | The software integration path runs on archived exploratory C5G7/OpenMC data. A physical improvement over a baseline has not been demonstrated. |
| 2. “Pemetaan QUBO Usmanov (fresh / once-burned / twice-burned) ke material UO₂/MOX C5G7 telah tervalidasi.” | **NOT SUPPORTED; wording must change** | The repository implements two separate formulations: a categorical burnup-state QUBO and a four-position, exactly-two-MOX C5G7 layout QUBO. The latter is explicitly not a mapping of the former. |
| 3. “Quantum advantage telah dibuktikan.” | **NOT ESTABLISHED; no hardware evidence** | QUBO encoding, exact classical enumeration, and classical simulated quantum annealing do not establish quantum-device execution or quantum advantage. |

These are evidence decisions, not judgments about whether the research direction is worthwhile. The three claims are not interchangeable and must not be combined into a single “validated” label.

## 1. Physical effectiveness of CB-PFR

### Existing evidence

- The integration smoke report records 18 archived corrected-seven-group C5G7/OpenMC statepoints: six layouts × three seeds.
- The statepoint hashes are unique and the MGXS hash is common across the dataset.
- All six layouts passed only the **illustrative** screening limits used to test the software path.
- Exact enumeration of the one-hot selector considered all 64 binary selector states and returned MUMU.
- The existing archived fixed-budget comparison reports that both CB-PFR and the point-estimate baseline select MUMU. It therefore does **not** show an incremental physical selection gain for CB-PFR.
- The transport settings were 100 batches, 10 inactive batches, and 1,000 particles per batch. These are exploratory smoke settings, not a demonstrated benchmark-grade convergence budget.

### Why the claim remains unproven

1. The screen uses illustrative limits (`k_eff` 1.13–1.22 and a fission-rate peaking proxy ≤2.0); these are not official C5G7 acceptance criteria or reactor-safety limits.
2. The fission-rate quantity is a proxy and the six material layouts are altered design variants. Their descriptive ranking is not itself a safety or design recommendation.
3. The current archive does not demonstrate a prespecified, justified physical objective and acceptance rule, a common high-fidelity compute budget, sufficient independent repetitions, uncertainty propagation, and a positive paired comparison against suitable baselines.
4. Even a better candidate score under an arbitrary screen would show only performance under that screen; it would not prove reactor safety or universal physical optimality.

### Minimum experiment to close this claim

1. Freeze the candidate set, objective(s), constraints, uncertainty handling, seeds, and compute budget before inspecting the final comparison.
2. Use the same corrected C5G7 model, cross-section data, and convergence settings for every layout and independent replicate. Save input hashes, seeds, logs, statepoints, and raw tally uncertainties.
3. Select a physically defensible objective. Report `k_eff`, its Monte Carlo uncertainty, and the defined spatial fission/power metric separately; do not treat a proxy as a safety criterion.
4. Run CB-PFR and at least a point-estimate baseline plus a fixed-margin or uncertainty-aware comparator on the exact same candidate data. Include QUBO energy only as a baseline if it has a meaningful, prespecified signal on that same problem.
5. Report selected candidate, feasibility, pairwise outcomes, effect sizes, uncertainty intervals, and failure cases. If methods choose the same layout, report no selection improvement.
6. Label the result “exploratory C5G7 computational comparison” unless benchmark-specific acceptance criteria and independent validation justify stronger wording.

**Current paper wording:** “CB-PFR was integrated with a separate C5G7 UO₂/MOX layout-selection prototype and evaluated on archived exploratory OpenMC outputs. These results verify pipeline operation; comparative physical effectiveness has not yet been established.”

## 2. Usmanov categorical QUBO versus C5G7 UO₂/MOX

### Code-level finding

- `src/cbpfr/qubo.py` defines three categorical states: `fresh`, `once_burned`, and `twice_burned`, represented through one-hot binary variables per core position, plus inventory and spatial penalties.
- `src/cbpfr/c5g7_design_qubo.py` defines four binary material-placement decisions, with (y_i=1) for MOX and (y_i=0) for UO₂, and enforces exactly two MOX assemblies. This produces six feasible layouts.
- The C5G7 module explicitly states that it is **not** a mapping of the legacy burnup-state QUBO. OpenMC transport results are external to that simple cardinality QUBO.

### Why a direct mapping is not validated

“Fresh/once-burned/twice-burned” denotes burnup history or state; “UO₂/MOX” denotes fuel composition/material category. They are different state variables. A scientifically defensible bridge would require a documented fuel-management model that maps burnup and isotopic composition to material definitions and cross sections, including relevant depletion assumptions and geometry. Relabeling the categories does not supply that bridge.

The separate C5G7 one-hot encoding is a valid exact encoding of the stated *two-MOX-of-four-position combinatorial constraint*. It is not, by itself, a physical fuel-performance objective, nor evidence that the legacy QUBO has been mapped or validated.

### Final disposition and replacement wording

Do not mark “the Usmanov QUBO-to-UO₂/MOX mapping is validated” as complete.

Use: “The legacy categorical burnup-state QUBO and the C5G7 UO₂/MOX placement study are treated as separate formulations. The C5G7 study uses an exact one-hot material-placement encoding with a fixed two-MOX cardinality constraint; a direct mapping from the legacy burnup labels to C5G7 materials has not been established.”

To reopen a direct mapping claim, define and test an explicit depletion/material-state mapping against documented physical inputs. If that is outside the paper's scope, retain the separate-formulation framing and close the audit as a **resolved limitation**, not as successful mapping validation.

## 3. Quantum advantage

### Evidence currently available

The repository contains QUBO formulations, exact classical enumeration for small problems, and classical simulated quantum annealing experiments. The recorded SQA run used 500 reads × 500 sweeps and found the exact ground state in 166/500 reads (33.2%); this is a classical simulation, not a physical quantum annealer.

### Required evidence for the requested claim

At minimum, a defensible quantum-advantage claim would need an archived run on an actual quantum device/annealer, exact submitted problem and embedding/chain details where applicable, returned samples and device metadata, repeatable quality/time-to-solution measurements, and a fair comparison with suitable classical solvers using matched problem instances, budgets, and tuning effort. A small problem solved exactly by enumeration is useful for validating the encoding but is not a meaningful quantum-advantage demonstration.

Benchmarking literature emphasizes application-appropriate instances, equitable solver tuning, and joint quality/cost measures rather than relying on “quantum” labels alone (see [Bucher et al., Towards Robust Benchmarking of Quantum Optimization Algorithms](https://arxiv.org/abs/2405.07624) and [Nature Reviews Physics, Benchmarking quantum computers](https://www.nature.com/articles/s42254-024-00796-z)).

### Final disposition and replacement wording

Do not claim quantum hardware was used or that quantum advantage was demonstrated.

Use: “The project formulates a constrained candidate-selection problem as QUBO and evaluates it using classical optimization/simulation tools. Quantum-device performance and quantum advantage were not evaluated.”

This claim cannot be converted into a positive result by writing more code for a classical SQA simulation. It requires actual device access and a fair benchmark. If that is not available for this submission, the scientifically correct endpoint is to leave the claim out of the paper.

## 4. Additional reproducibility correction

The confirmatory synthetic benchmark script on `research/fixed-budget-ranking-selection-benchmark` had a stale metric label: `nominal_95pct_lower_bound_empirical_coverage`. Because `estimate - 1.96 × reported_se` is a one-sided lower bound corresponding to nominal 97.5% one-sided coverage under calibrated Gaussian assumptions, the key has been corrected to `nominal_97_5pct_one_sided_lower_bound_empirical_coverage` in commit [092c44f](https://github.com/thenextw4ng/cb-pfr/commit/092c44f32f878e6d55cd92a7131ba1098ce4a778). The workflow triggered by that commit must finish and its artifact be reviewed before reporting confirmatory synthetic metrics. This correction does not alter the benchmark's thresholds, random seeds, scenarios, or selection rules.

The confirmatory benchmark completed successfully on GitHub Actions (run [38122708676](https://github.com/thenextw4ng/cb-pfr/actions/runs/38122708676)); the raw CSV and JSON summary were downloaded and reviewed. Across 40,000 synthetic pools, CB-PFR improved selected true-feasibility by +0.4875 percentage points over both point-estimate selection and uniform margin (paired 95% CIs +0.3725 to +0.6000 pp and +0.3700 to +0.6025 pp; Holm-adjusted McNemar p = 1.165×10⁻¹⁶ for each). This fails the preregistered ≥2 pp practical-effect threshold, so the protocol returns `prespecified_synthetic_advantage_supported = false`. There was no selection-feasibility gain in the calibrated homoscedastic or shifted/near-threshold scenarios. Empirical lower-bound coverage fell to 83.58% when reported uncertainty was halved and 73.42% under the shifted scenario, illustrating calibration sensitivity. Full results and hashes are in [the confirmatory results report](https://github.com/thenextw4ng/cb-pfr/blob/research/fixed-budget-ranking-selection-benchmark/reports/CB_PFR_RS_SYNTHETIC_CONFIRMATORY_RESULTS_2026-10-11.md). The benchmark is synthetic only. Its point-estimate baseline is a fixed-pool comparator, not an adaptive sequential ranking-and-selection algorithm. These results do not support general or physical superiority.

## 5. Final publication checklist

- [x] Audit the three exact claims against the code and current evidence.
- [x] Identify the precise reason the legacy burnup QUBO and C5G7 material QUBO are separate formulations.
- [x] Record that the archived physical integration smoke test is not evidence of comparative physical improvement.
- [x] Record that classical SQA and QUBO encoding are not quantum advantage.
- [x] Correct the stale synthetic coverage metric label.
- [x] Review the corrected confirmatory synthetic workflow output and raw artifact before quoting results.
- [ ] Run and audit a predeclared, higher-budget C5G7 candidate comparison before making a physical-effectiveness claim.
- [ ] Obtain actual quantum-device results and conduct a fair classical benchmark before making a quantum-advantage claim.

## Final decision

For the current evidence set, **none of the three original claims is cleared as written**. Claim 2 can be resolved for this submission by using the accurate separate-formulation wording. Claim 1 remains a targeted experimental question that can be tested with a properly designed C5G7 comparison. Claim 3 remains out of scope unless real device evidence becomes available. The paper can still make a defensible contribution about CB-PFR as a proposed uncertainty-aware post-optimization selection method, its reproducible synthetic evaluation, and the implementation of a separate QUBO-based C5G7 layout-selection prototype.
