# C5G7 validation gates and QUBO-to-design mapping

## Decision

The three outstanding items are now separated into executable software gates and scientific review gates. The repository can encode and enumerate the six four-position UO2/MOX arrangements exactly, and it can audit repeated OpenMC results. It cannot honestly convert the legacy `fresh / once_burned / twice_burned` labels into C5G7 materials: those labels describe burnup categories, while C5G7 defines specified UO2/MOX enrichment/material compositions. No equivalence is established by sharing a categorical representation.

## 1. A defensible mapping that is possible now

A **new, explicitly separate** four-position design QUBO uses one binary variable per assembly position:
- `y_i = 0`: UO2 assembly at position i.
- `y_i = 1`: MOX assembly at position i.
- Exactly two positions must be MOX; the remaining two are UO2.

The exact-cardinality penalty is

[
H_{mathrm{count}}(y)=Aleft(sum_{i=1}^{4}y_i-2ight)^2,quad A>0.
]

Its upper-triangular QUBO expansion is

[
H_{mathrm{count}}(y)=4A-3Asum_i y_i+2Asum_{i<j}y_i y_j.
]

For binary y, the energy is zero exactly when there are two MOX assemblies. There are ({4choose2}=6) feasible layouts, which match the six layouts enumerated for the transport study. This is a rigorous encoding of the **material-count constraint only**; it is not a surrogate for k-effective or power, and it does not establish that any layout is physically preferable. OpenMC must score each feasible layout.

The implementation is `src/cbpfr/c5g7_design_qubo.py`. Tests exhaust all (2^4=16) binary vectors, verify the expansion, and check the six feasible layouts.

## 2. Benchmark-grade work: staged protocol

The proposed protocol is machine-readable in `config/benchmarks/c5g7_validation_protocol.json`. It is explicitly a **project screening protocol**, not an official OECD/NEA acceptance specification.

### Gate G0 — exact model identity (blocking)

Before numerical benchmark acceptance, compare the canonical generated geometry, material compositions, settings, boundary conditions, group structure, and nuclear-data provenance to the chosen primary specification. In particular, reconcile production-versus-smoke materials XML. Keep exact input hashes and the upstream commit in the run manifest. A close k-effective value is a useful sanity check but cannot substitute for this review.

### Gate G1 — canonical k-effective screening

The primary reference cited in the existing validation report is (k_{mathrm{eff}}=1.18655), with a reported standard uncertainty near 9.5 pcm. The protocol proposes an internal screening threshold of at most 100 pcm absolute difference, a difference within two combined standard uncertainties, a per-run reported standard deviation no greater than 10 pcm, and at least three unique seeds. These thresholds are provisional project gates, **not official benchmark acceptance limits**. G1 remains blocked until G0 passes.

The current production baseline's reported standard deviation is about 5.61 pcm, but its model identity is not yet fully reviewed. Therefore the scalar comparison alone does not pass G1.

### Gate G2 — spatial tallies

The current archived tallies include flux, fission, and nu-fission mesh scores; those are not automatically normalized power. Select the benchmark-compatible spatial quantity and normalization, retrieve the matching reference distribution, and report RMS and maximum relative error with uncertainty. The provisional 2% RMS / 5% maximum limits in the JSON must be replaced if the primary benchmark specifies a different metric or acceptance criterion.

### Gate G3 — repeated candidate runs

The initial smoke study has three seeds per layout, but only 100 batches, 10 inactive, and 1,000 particles per batch. The protocol proposes an intermediate 2,000/100/5,000 screen with three seeds per layout. This is a proposed next budget, **not an executed result and not guaranteed to be converged**. Use a pilot, inspect inactive-batch convergence and the standard error, then increase histories until the predeclared criteria are met. Candidates whose ranking is unresolved within combined uncertainty need higher-budget confirmation.

### Gate G4 — objective before ranking

The six layout results must not be optimized by simply choosing the highest or lowest k-effective. The physical objective, hard constraints, and acceptable operating region must be reviewed and fixed before inspecting final ranking. Without a justified objective, report descriptive candidate responses and uncertainty only.

## 3. Current status

- **Completed in code:** exact 4-variable material-count QUBO, six feasible assignments, exhaustive tests.
- **Specified:** staged model-identity, scalar, tally, repeated-run, and objective gates.
- **Still blocked:** independent G0 model review, matching spatial reference data, actual intermediate/high-budget runs, and approval of the physical objective.
- **Legacy mapping:** still correctly marked `NO_DEFENSIBLE_MAPPING_FOUND`. The new assembly-placement QUBO is a separate model and must not be described as solving the original burnup-state QUBO.

## Reproduction

Run the automated tests with `python -m unittest discover -s tests -v`. The validation protocol is `config/benchmarks/c5g7_validation_protocol.json`.
