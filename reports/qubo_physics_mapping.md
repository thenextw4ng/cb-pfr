# QUBO-to-physics mapping audit

## Status: NO_DEFENSIBLE_MAPPING_FOUND

The executable model uses seven abstract positions and categories fresh, once_burned, and twice_burned. It has 21 binary variables and 20 feasible vectors after exact enumeration.

The project must not translate those labels into C5G7 UO2/MOX material categories. C5G7 benchmark material/enrichment categories are not equivalent to fresh/once-/twice-burned states.

A defensible mapping would require:
1. physical position/geometry definitions;
2. documented material or depletion states;
3. a category-to-material rule for every candidate position;
4. nuclear-data provenance;
5. objective/constraint limits and an independent validation reference.

Until these are supplied, physical candidate evaluation is blocked. The OpenMC boundary in src/cbpfr/openmc.py therefore fails closed and emits an abstract candidate manifest rather than fabricated material cards.
