# Local QAOA Experiment on a Synthetic Cardinality-Constrained QUBO

**Date:** 2026-10-16  
**Classification:** Local simulator experiment / software-mechanics evidence  
**Hardware submission:** No  
**Physical CB-PFR integration:** Not established

## Executive result

A local NumPy statevector implementation of depth-2 QAOA was run against the stored (n=10) synthetic QUBO instance. The reported best measured bitstring reached the exact constrained optimum, (-23). However, the classical differential-evolution parameter optimizer did **not** meet its termination criterion, and the expected penalized energy at its reported parameters was (119.2042). The observed optimum is therefore a successful finite-shot sample, not evidence that the parameter optimization converged or that QAOA outperformed a classical baseline.

## Problem definition

The binary objective is

\[
f(x)=\sum_i h_i x_i+\sum_{i<j}w_{ij}x_ix_j, \quad x_i\in\{0,1\},
\]

with the exact-cardinality constraint \(\sum_i x_i=5\). The stored instance contains 10 variables and 252 feasible bitstrings. Exhaustive enumeration reports an exact feasible optimum of \(-23\), at:

\[
[0,1,1,1,1,0,0,0,1,0].
\]

This is a **synthetic combinatorial instance**, not the four-fuel-position C5G7 model. The coefficients are not physical nuclear data and have no validated mapping to MOX/UO₂ configurations.

## Mapping and penalty checks

The objective's absolute coefficient bound is \(B=139\). The implementation used \(A=2B+1=279\) for the penalty \(A(\sum_i x_i-k)^2\), with \(k=5\).

| Check | Recorded result |
|---|---:|
| Computational-basis bitstrings checked | 1,024 |
| Maximum absolute QUBO–Ising energy mismatch | 0.0 |
| Tolerance | \(10^{-9}\) |
| Algebraic mapping check | PASS |

This supports algebraic consistency of the implemented QUBO-to-Ising expansion for this synthetic instance. It does not verify the suitability of the objective for reactor physics.

## Local QAOA settings and measured result

| Setting / metric | Recorded value |
|---|---:|
| Simulator | NumPy statevector |
| QAOA depth | \(p=2\) |
| Seed | 20261016 |
| Shots | 4,096 |
| Optimizer | SciPy differential evolution |
| Objective evaluations | 2,495 |
| Optimizer termination | **Not successful** — maximum iterations exceeded |
| Expected penalized energy at returned parameters | 119.2042438291 |
| Best sampled bitstring | `[0,1,1,1,1,0,0,0,1,0]` |
| Best sampled objective / penalized energy | −23 |
| Best sampled state feasible | Yes (five ones) |
| Gap to exact constrained optimum | 0 |
| Feasible shots | 2,507 / 4,096 |
| Feasibility rate | 61.2061% |
| Best-state count | 10 / 4,096 (0.2441%) |

The baseline's separate 1,000-sample random-feasible experiment recorded five optimum hits (0.5%). The QAOA sample count corresponds to 0.2441% of all QAOA shots, or 0.399% conditional on the 2,507 feasible shots. This is only a descriptive comparison across one run and different sampling protocols; it does not establish a statistically reliable performance difference. No QAOA advantage over classical search is demonstrated.

## What this result does and does not establish

**Established for this run**
- The local script loaded the stored synthetic (n=10) coefficients.
- The reported QUBO-to-Ising energy mapping matched on all 1,024 bitstrings within the declared tolerance.
- The finite-shot sample included a feasible state at the known exact optimum.
- The run did not submit work to IBM Quantum hardware.

**Not established**
- Successful convergence of the QAOA parameter optimizer.
- Performance improvement over random search, simulated annealing, or another properly budget-matched classical baseline.
- Execution on a quantum processing unit or quantum advantage.
- A QUBO-to-C5G7 physical mapping, OpenMC evaluation of this synthetic sample, or physical validation of CB-PFR.
- A physically optimal reactor fuel configuration.

The repository's separate C5G7 study uses four fuel positions with exactly two MOX and two UO₂, and its current composition-only QUBO ties all six feasible arrangements. This (n=10) synthetic instance must not be substituted for that physical formulation. It can be retained only as a separate local algorithm/software smoke experiment.

## Provenance

The originally supplied local artifacts were reviewed without rerunning the QAOA optimizer. SHA-256 fingerprints of those exact uploaded files:

| Uploaded artifact | SHA-256 |
|---|---|
| `qaoa_local_test_results.json` | `52672b5755f6321ac4b6121f3e4a8edb157ba49d627ca6177bf317fadde83b9c` |
| `qaoa_local_test.py` | `7e5a562011fe9384221375ca7d1c6f616f7d261a5ad64bfb1bc850a6ed99e` |
| `qubo_baseline_results.json` | `8b677814ea5dcd850aaa1020cb9f99881cf28ebcba7b9870c6e6d2dd351a0abf` |

The archived input and result summaries are stored alongside this report under `experiments/local_qaoa_synthetic_qubo_20261016/`. The (n=10) input JSON is an extracted snapshot of the larger original baseline, not a replacement for that original file.

## Recommended claim wording

> A local statevector QAOA implementation was exercised on a synthetic 10-variable cardinality-constrained QUBO. Its QUBO-to-Ising mapping passed exhaustive algebraic checks, and one finite-shot sample reached the known feasible optimum. The parameter optimizer did not meet its termination criterion, and the experiment does not demonstrate quantum-hardware execution, a classical-baseline improvement, or physical CB-PFR validation.

