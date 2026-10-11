# Architecture and data flow

## Existing layers

1. **Abstract optimization:** `src/cbpfr/qubo.py` represents categorical fresh/once-burned/twice-burned states and constraints on an abstract core graph.
2. **Separate C5G7 layout encoding:** `src/cbpfr/c5g7_design_qubo.py` represents four assembly positions with exactly two MOX and two UO2 assemblies. It enumerates six layouts. It is deliberately not a translation of the abstract burnup-state model.
3. **Transport execution:** `scripts/run_c5g7_layout_study.py` stages a pinned upstream MIT-CRPG C5G7 model, patches the group boundaries and layout, runs OpenMC, and records hashes and statepoint paths.
4. **Physical metrics:** `scripts/analyze_c5g7_assembly_fission.py` integrates mesh fission-score means into assembly totals and calculates a dimensionless assembly peaking proxy.
5. **Replicate uncertainty:** `scripts/aggregate_c5g7_fission_replicates.py` aggregates derived metrics from distinct seeds and unique statepoints.
6. **Reference comparison:** `scripts/compare_c5g7_reference.py` compares (k_{eff}) with the single published canonical baseline and blocks the mismatched pin-power/assembly-peaking comparison.
7. **Selection/ranking:** `src/cbpfr/ranking.py` ranks candidate objects using QUBO feasibility and explicitly supplied metric limits/uncertainty. This is not a reactor safety method.
8. **UI:** `app.py` and the API docs expose a research prototype. They must not label a candidate physically validated unless a validation evidence manifest supports that status.

## Evidence flow

`QUBO vector -> candidate layout -> source-patched geometry -> OpenMC inputs -> statepoint -> raw-HDF5 audit -> assembly tally -> replicate aggregation -> metric-aware reference comparison -> status/ranking`

Each transition needs candidate ID, layout signature, seed, input hash, statepoint hash, code revision, and observable definition. The current QUBO-to-transport relationship is only defensible for the separate four-position UO2/MOX design encoding under its declared toy layout assumptions. The legacy categorical burnup QUBO has no approved C5G7 material mapping.

## UI service boundary

UI should call a small service layer rather than construct geometry or run tally logic itself. Stable service operations should include configuration validation, candidate enumeration, run submission/status, result retrieval, ranking, validation status, and report export. Return execution status separately from validation status; missing data should produce `VALIDATION_BLOCKED`, not a guessed rank or green validation badge.
