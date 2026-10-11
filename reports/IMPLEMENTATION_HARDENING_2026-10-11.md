# C5G7 selection hardening — 2026-10-11

## Changes

The candidate-selection QUBO builder now fails closed on non-finite bounds and weights, non-positive physical summary values, missing candidate/layout labels, duplicate layout signatures, fewer than three runs per candidate, and non-finite objective scores. The evaluator rejects Boolean values as solver bits.

## Scientific boundary

Three runs are only an initial replication floor, not a convergence certificate or benchmark acceptance. `n_runs` is a summary field and cannot itself prove seed independence; the run-level evidence audit must still verify unique seeds, unique statepoint hashes, standard-group audit, and consistent model identity. The builder does not select a winner when no candidate lies fully inside the explicitly supplied k-effective band. The legacy burnup-state QUBO remains unmapped to C5G7 UO2/MOX.

## Remaining external gates

1. Review the canonical C5G7 geometry, material definitions, nuclear data, and standard seven-group boundaries against the primary benchmark specification.
2. Run the corrected canonical high-budget workflow on an available OpenMC runner and preserve its artifact.
3. Review the mesh-to-assembly fission tally mapping and define a physically justified objective/acceptance band before design ranking.
4. Treat the six-layout corrected-group smoke study as exploratory until convergence and benchmark criteria are satisfied.

No reactor-safety or benchmark-validation claim is made by this software hardening change.
