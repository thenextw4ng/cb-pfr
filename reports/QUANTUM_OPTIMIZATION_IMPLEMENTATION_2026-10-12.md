# Quantum optimization implementation update
**Date:** 2026-10-12  
**Branch:** `feature/step05-scientific-integration`  
**Pull request:** https://github.com/thenextw4ng/cb-pfr/pull/45

## Implemented in this branch

- `src/cbpfr/solvers.py`: guarded exhaustive binary reference solver; conversion from the repository's upper-triangular QUBO to Ocean-compatible QUBO dictionaries; optional sampler adapter; explicit solver taxonomy and sample provenance.
- `src/cbpfr/pipeline.py`: strict solver-output to candidate to physics-evaluation to CB-PFR orchestration. It rejects mismatched solver identity, variable count, duplicate solver IDs, altered candidate vectors, and candidate IDs that are not in the solver output. Decision bundles include the solver run and a deterministic SHA-256.
- `pages/02_Quantum_Optimization.py`: dedicated QUBO/quantum optimization workstation. It exposes the 4-variable C5G7 encoding, 16 binary states, six feasible layouts, QUBO coefficients, optional classical Ocean simulated annealing, and the handoff to physics evaluation.
- `tests/test_solvers.py` and `tests/test_pipeline.py`: tests for exact reference solving, energy/offset mapping, solver taxonomy, solver-run provenance, and fail-closed joins.
- `docs/QUANTUM_OPTIMIZATION_ARCHITECTURE.md`: solver taxonomy, architecture, and scientific guardrails.

## What is and is not quantum

The default solver in this code is exact classical enumeration. The optional Ocean adapter can call a user-supplied sampler; the adapter itself does not decide whether the backend is a QPU. An actual quantum-annealer run requires configured provider credentials and retained provider run metadata. The current branch does not claim that a QPU was used.

## Formulation finding that shapes the UI

The existing C5G7 QUBO only penalizes violations of exactly two MOX assemblies. The six feasible layouts all tie in this objective; the QUBO does not include OpenMC response metrics. The correct workflow is therefore to generate/verify candidate layouts, evaluate them using a frozen physical-simulation protocol, then rank using CB-PFR. Choosing a physically superior layout from this QUBO energy alone would be invalid.

## Verification status

The branch has an open draft pull request so repository CI can validate the changes. At the time of this report, no passing CI result has been observed through the available status endpoint. Network access from the local execution container was unavailable, so the new tests have not been independently run in that container. No OpenMC simulation or QPU execution was started.
