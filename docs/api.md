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
