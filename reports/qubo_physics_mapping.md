# QUBO-to-physics mapping audit

## Status: NO_DEFENSIBLE_MAPPING_FOUND (unchanged after Phase 3 benchmark selection)

The executable model uses seven abstract positions and categories fresh, once_burned, and twice_burned. It has 21 binary variables and 20 feasible vectors after exact enumeration.

The project must not translate those labels into C5G7 UO2/MOX material categories. C5G7 benchmark material/enrichment categories are not equivalent to fresh/once-/twice-burned states.

A defensible mapping would require:
1. physical position/geometry definitions;
2. documented material or depletion states;
3. a category-to-material rule for every candidate position;
4. nuclear-data provenance;
5. objective/constraint limits and an independent validation reference.

Phase 3 selected the OECD/NEA C5G7 family only as a documented transport-code reference framework; it does not provide a burnup-management mapping. The decision, source URLs, and explicit exclusions are recorded in [benchmark_selection_c5g7.md](benchmark_selection_c5g7.md) and [config/benchmarks/c5g7_manifest.json](../config/benchmarks/c5g7_manifest.json). An automated fail-closed gate is available via `scripts/audit_benchmark_manifest.py`. It is expected to report `blocked` until actual model inputs, reviewed reference data, nuclear-data provenance, position mapping, and state-to-material mapping are supplied. This is intentional: the OpenMC boundary in src/cbpfr/openmc.py continues to emit an abstract candidate manifest rather than fabricated material cards.
