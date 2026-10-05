# Methodology

CB-PFR is a post-optimization ranking layer. A QUBO stage supplies candidate configurations; CB-PFR evaluates supplied metric estimates and uncertainty magnitudes against predeclared limits.

For metric j and candidate i:

[
B^-_{i,j}=hatmu_{i,j}-z_jhat s_{i,j},qquad
B^+_{i,j}=hatmu_{i,j}+z_jhat s_{i,j}.
]

The raw violation is

[
v_{i,j}=max(0,L_j-B^-_{i,j})+max(0,B^+_{i,j}-U_j),
]

followed by scale normalization and weighted aggregation.

The implementation deliberately does **not** infer that an arbitrary `z` multiplier is a confidence interval. `MetricLimit.bound_kind` records provenance, and the default is `operational_heuristic`.

The final selection is lexicographic: QUBO feasibility first, then conservative physical feasibility, aggregate violation, QUBO energy, and input index. This makes the tie-breaking rule deterministic.

## Scope boundary

The current toy QUBO has 21 binary variables and 20 feasible vectors. Its `fresh`, `once_burned`, and `twice_burned` labels are abstract categories. The released physics audit reports `NO_DEFENSIBLE_MAPPING_FOUND` to C5G7 transport materials. Therefore the package must not be described as a validated reactor fuel-loading optimizer.
