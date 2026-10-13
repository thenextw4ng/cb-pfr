# Quantum optimization architecture for CB-PFR
**Date:** 2026-10-12  
**Branch:** feature/step05-scientific-integration

## Purpose

Make optimization a first-class, auditable stage in the CB-PFR platform while keeping solver claims honest. A QUBO formulation is an optimization model, not proof that quantum hardware ran and not a physical reactor objective by itself.

## End-to-end architecture

1. **Formulation identity:** assign a stable formulation ID and candidate-encoding ID. The legacy Usmanov-style categorical burnup QUBO and the four-position C5G7 UO₂/MOX placement QUBO remain separate models.
2. **Solver execution:** save solver name, solver class, backend, requested reads, elapsed time, seed when supported, sample counts, and solver output. The new `cbpfr.solvers` module provides an exact classical reference solver and an optional adapter for Ocean-compatible samplers.
3. **Candidate feasibility:** independently recalculate QUBO energy and the formulation's hard constraints. Solver-reported energy alone is not treated as the only integrity check.
4. **Physics evaluation:** evaluate each candidate with a separately versioned OpenMC model or a sourced experimental/benchmark dataset. Keep each candidate's uncertainty semantics, units, seed, and data hash.
5. **CB-PFR decision layer:** rank only after every candidate has a complete evaluation record matching the declared metrics and limits.
6. **Decision evidence bundle:** export the formulation identity, solver metadata, candidate records, provenance, ranking output, and a stable hash.

## Solver taxonomy

| Solver class | Meaning | What may be claimed |
|---|---|---|
| `classical_exact` | Exhaustive search over all bitstrings; guarded by a variable limit | Exact optimum only for the stated finite QUBO and search space |
| `classical_heuristic` | Classical heuristic solver | Heuristic result with settings and run evidence |
| `classical_simulated_annealing` | Classical simulated annealing, including Ocean's simulated annealing sampler | Classical stochastic optimization |
| `classical_simulated_quantum_annealing` | Classical algorithm that simulates selected quantum-annealing effects | Quantum-inspired/simulated method, not QPU execution |
| `quantum_annealer` | Actual configured quantum annealing hardware | QPU execution only if provider/backend run evidence is retained |
| `external` | Solver outside the recognized categories | Describe the exact tool and evidence; do not infer hardware |

The Ocean adapter accepts an explicitly supplied sampler. It does not provision credentials or assert the backend is quantum. Caller-supplied solver metadata must match the actual backend and should be audited against returned provider logs.

## Important formulation finding: C5G7 QUBO is currently a feasibility generator

The existing four-position C5G7 objective is:

`E(y)=A(\sum_i y_i-2)^2`, with (y_i=1) for MOX and (0) for UO₂.

This encodes exactly two MOX assemblies. It does **not** include (k_\mathrm{eff}), fission-rate distribution, or any OpenMC tally. Therefore all six feasible assignments have equal QUBO energy. A solver cannot select the physically best candidate from this objective alone. The scientifically defensible path is to generate/verify the six feasible layouts, evaluate them with the same frozen physics protocol, then compare candidates using declared observables and CB-PFR.

Do not append simulator results to the QUBO objective unless a scientifically justified and validated objective/constraint mapping is separately designed. The current candidate-selection workflow is post-optimization, not an integrated physics-informed QUBO.

## User interface

A new Streamlit page, `pages/02_Quantum_Optimization.py`, exposes:
- the C5G7 encoding and upper-triangular QUBO coefficients;
- the full 16-state binary space and six feasible layouts;
- the explicit energy tie among feasible layouts;
- optional Ocean classical simulated annealing when `dimod` is installed;
- a handoff map from QUBO/solver output to physics evaluation and CB-PFR.

The page does not launch OpenMC, access a QPU, or claim quantum advantage. A future QPU UI must require a configured sampler and preserve solver ID, QPU timing, reads, chain-break statistics where applicable, embedding/solver parameters, returned samples, and provider run ID.

## Validation boundary

Unit tests cover the exact reference solver, QUBO coefficient/offset mapping, solver taxonomy validation, experiment provenance, and fail-closed candidate/evaluation joins. CI still needs to run on the branch before the changes can be considered verified. No OpenMC run or QPU execution was performed by this change.
