# Classical vs QUBO-encoded simulated annealing: execution report

- **Study ID:** `CBPFR-classical-vs-QUBO-SA-equal-energy-eval-2026-10-16`
- **Source run:** [GitHub Actions run 38829683683](https://github.com/thenextw4ng/cb-pfr/actions/runs/38829683683)
- **Artifact:** `cbpfr-classical-vs-qubo-equal-budget-2026-10-16` (artifact ID 12016996172)
- **Status:** completed; script compilation, research unit tests, benchmark execution, and artifact upload all succeeded.
- **Environment:** Python 3.12.15, Linux x86_64.

## Design

Ninety synthetic random quadratic binary instances were evaluated: 30 each at 10, 14, and 18 binary variables. Every instance enforced \\(\\sum_i x_i=n/2\\). Two methods each received 5,000 objective/energy evaluations per instance:

1. **Classical feasible random search:** sample only feasible cardinality-​\(n/2\) states and retain the lowest objective.
2. **QUBO + classical simulated annealing:** add penalty \\(A(\\sum_i x_i-n/2)^2\\), with \\(A=2(\\sum_i |h_i|+\\sum_{i<j}|J_{ij}|)+1\\), then optimize with simulated annealing.

Exact enumeration of all feasible states was used only as an oracle for objective-gap measurement; its work was not charged to either heuristic's budget. This equalizes evaluation counts, not wall-clock time or work per evaluation.

## Results

| Variables | Method | Mean absolute objective gap | 95% bootstrap CI for mean gap | Exact-oracle match rate | Mean runtime per instance |
|---:|---|---:|---:|---:|---:|
| 10 | Classical feasible random search | 0.0000 | [0.0000, 0.0000] | 100.0% | 0.0629 s |
| 10 | QUBO + classical simulated annealing | 1.0012 | [0.6888, 1.3312] | 20.0% | 0.0141 s |
| 14 | Classical feasible random search | 0.0448 | [0.0042, 0.0985] | 86.7% | 0.0975 s |
| 14 | QUBO + classical simulated annealing | 2.3253 | [1.8544, 2.7952] | 10.0% | 0.0155 s |
| 18 | Classical feasible random search | 0.9677 | [0.6996, 1.2438] | 20.0% | 0.1387 s |
| 18 | QUBO + classical simulated annealing | 4.5174 | [3.8096, 5.2565] | 0.0% | 0.0171 s |

Paired gap difference (QUBO-SA minus feasible random search):

| Variables | Mean paired difference | 95% paired-bootstrap CI | QUBO-SA better on instances | QUBO-SA exact |
|---:|---:|---:|---:|---:|
| 10 | 1.0012 | [0.6929, 1.3350] | 6.7% | 20.0% |
| 14 | 2.2805 | [1.8006, 2.7616] | 3.3% | 10.0% |
| 18 | 3.5496 | [2.8719, 4.2636] | 0.0% | 0.0% |

All methods found at least one feasible state in every instance. The full run-level and paired tables are preserved in the linked Actions artifact.

## Interpretation and limitations

- On these 90 synthetic instances and this frozen parameterization, the direct feasible random-search baseline achieved smaller objective gaps than QUBO-encoded simulated annealing at the same number of evaluations. The observed paired-bootstrap intervals for the gap difference were positive at all three tested sizes.
- The simulated-annealing method is **classical**. No quantum hardware or quantum annealing was used; this is not a quantum-advantage experiment.
- The comparison is not runtime-matched: simulated annealing was faster in these runs, while the direct method had better objective gaps. Evaluation count does not equal total compute cost.
- The instances are synthetic and do not contain an OpenMC-derived physical objective. These results cannot establish that QUBO, CB-PFR, or any fuel layout is physically superior.
- The separate four-position C5G7 cardinality penalty enforces exactly two MOX positions, but all six feasible layouts have equal penalty energy. It cannot physically rank those six layouts without a separately justified objective.
- This is a bounded baseline study, not a universal claim about QUBO or quantum optimization. Further solver comparisons should include tuned parameters, multiple independent algorithm seeds, and clearly specified runtime/evaluation accounting before stronger claims.

## Evidence links

- [Workflow run](https://github.com/thenextw4ng/cb-pfr/actions/runs/38829683683)
- [Frozen experiment protocol](../docs/experiments/CBPFR_C5G7_CONVERGENCE_SELECTION_QUBO_PROTOCOL_2026-10-16.md)
- [Benchmark implementation](../scripts/run_classical_vs_qubo_benchmark.py)
