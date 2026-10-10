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

## Alternative reformulation added in Phase 4

The old mapping remains blocked by design. A separate, explicit C5G7 assembly-placement problem has now been specified in [phase4_c5g7_reformulation.md](phase4_c5g7_reformulation.md), with a generator at `scripts/enumerate_c5g7_layouts.py`. It uses C5G7's UO2/MOX assembly labels directly, enumerates six placements of two UO2 and two MOX assemblies in the source model's four fuel positions, and keeps reflector positions fixed. It does **not** relabel the old burnup categories or claim a physical ranking.

This alternative removes the semantic mapping error by defining a new decision problem. It does not remove the need to run a verified transport model or compare against the primary benchmark data. The original QUBO's physical mapping status remains `NO_DEFENSIBLE_MAPPING_FOUND`.
