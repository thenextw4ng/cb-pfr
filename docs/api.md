# API surface

The public research API is intentionally small.

- MetricLimit: declares a metric limit, uncertainty semantics, scale, weight, and bound provenance.
- PhysicalEstimate: supplies candidate-specific metric estimates and uncertainty magnitudes.
- rank_all_methods(...): compares QUBO-only, point-estimate, CB-PFR, and uniform-margin ranking on one candidate pool.
- selected_is_conservatively_feasible(...): explicit pass/fail helper for a selected result.
- CoreSpec: declares the abstract graph, regions, inventory, and optional symmetry pairs.
- build_usmanov_style_qubo(...): expands the abstract constraint formulation into an upper-triangular QUBO.
- enumerate_feasible_candidates(...): exact enumeration for small verification instances.
- preflight_openmc(...): checks for an externally supplied OpenMC model without fabricating one.
- candidate_loading_manifest(...): produces an abstract mapping manifest and explicitly blocks physical handoff until provenance exists.

The API is not a reactor-engineering interface. Physical semantics must be supplied by a documented external benchmark.

## C5G7 evidence API / command contracts

- `scripts/aggregate_c5g7_fission_replicates.py --inputs <report...> --out <new-file.json>` aggregates derived metrics across independent statepoints. Reports must contain distinct integer seeds and distinct statepoint SHA-256 values.
- `scripts/compare_c5g7_reference.py --simulation-json <assembly_fission.json> --reference-csv examples/c5g7_published_reference_baseline.csv --out <new-file.csv>` records a (k_{eff}) numerical screen and blocks non-comparable power metrics.
- Analysis output distinguishes run completion from validation. A technical pass is not an `INDEPENDENTLY_VALIDATED` status.

The dashboard can be developed as a research UI, but physical validation status must be sourced from an explicit evidence manifest and default to blocked when evidence is missing.
