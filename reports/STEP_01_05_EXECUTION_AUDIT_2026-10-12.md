# Step 01–05 implementation and evidence audit
**Date:** 2026-10-12  
**Repository:** `thenextw4ng/cb-pfr`  
**Working branch:** `feature/step05-scientific-integration`  
**Pull request:** https://github.com/thenextw4ng/cb-pfr/pull/45

## Executive outcome

Steps 01–05 have been advanced on an isolated branch; main remains untouched. This is a software and evidence-contract implementation, not a claim that a new OpenMC run or QPU run occurred.

### Changes made
- `src/cbpfr/experiment.py`: versioned experiment metadata, evaluation records, explicit metric units/uncertainty semantics, fail-closed candidate/evaluation matching, source-kind separation, ranking orchestration, and stable bundle hashing.
- `src/cbpfr/solvers.py`: exact classical reference solver, upper-triangular QUBO conversion, and optional adapter for a user-supplied Ocean-compatible sampler.
- `src/cbpfr/pipeline.py`: strict solver-output → candidate → evaluation → CB-PFR orchestration with solver identity and vector matching, and a hashed decision bundle.
- `pages/02_Quantum_Optimization.py`: dedicated QUBO/quantum optimization workstation.
- Tests: `tests/test_experiment_contract.py`, `tests/test_solvers.py`, and `tests/test_pipeline.py`.
- Documentation: `docs/QUANTUM_OPTIMIZATION_ARCHITECTURE.md` and `reports/QUANTUM_OPTIMIZATION_IMPLEMENTATION_2026-10-12.md`.
- Package version synchronized to 0.3.0 in `pyproject.toml` and `src/cbpfr/__init__.py`.

## Step 01 — Repository and claim audit

### Existing architecture found
- `src/cbpfr/qubo.py`: categorical burnup-state QUBO with fresh / once-burned / twice-burned labels and constraint penalties.
- `src/cbpfr/c5g7_design_qubo.py`: separate four-position C5G7 UO₂/MOX placement encoding with exactly two MOX assemblies; six feasible layouts.
- `src/cbpfr/ranking.py`: CB-PFR conservative feasibility ranking and point-estimate / uniform-margin / QUBO-only comparators.
- `src/cbpfr/integration.py`: existing adapter from QUBO candidates and physical estimates to rankings.
- `src/cbpfr/openmc.py`: OpenMC preflight, candidate manifest and statepoint/keff parsing helpers; it does not infer materials or geometry from burnup labels.

### Evidence constraints that remain binding
1. The 40,000-pool confirmatory synthetic study did not reach its predeclared practical-effect threshold of +2 percentage points. It is not evidence of general or physical superiority.
2. The archived C5G7 18-statepoint selection smoke demonstrates pipeline operation under illustrative limits, not benchmark-grade physical validation. CB-PFR and the point-estimate baseline selected the same layout in the recorded comparison.
3. The BEAVRS experimental spatial-map comparison had poor spatial agreement and is not successful physical validation.
4. The legacy burnup-state QUBO and C5G7 material-placement QUBO are different formulations. No material/depletion mapping was silently added.
5. Exact enumeration and classical simulated quantum annealing are not quantum-device execution and do not establish quantum advantage.

## Step 02 — Dataset and evidence-source plan

The integration contract distinguishes `synthetic`, `mock`, `openmc_statepoint`, `experimental_measurement`, and `benchmark_reference` sources. Comparisons cannot silently mix these kinds.

### Candidate sources to audit before use
- Existing repository C5G7/OpenMC statepoints and manifests: available for provenance/integrity work; currently exploratory evidence.
- BEAVRS Cycle 1 day-0 experimental detector map and pinned upstream model: current spatial agreement is poor, so do not use it as a validation success.
- BRIN's *Atom Indonesia* paper on neutron-flux measurement at RSG-GAS with foil-activation benchmarking: https://atomindonesia.brin.go.id/index.php/aij/article/view/1768. This is a source lead, not confirmation that raw measurements are downloadable or compatible.
- IAEA research-reactor computational benchmarking report: https://www-pub.iaea.org/MTCD/Publications/PDF/TE-1879_web.pdf.
- IAEA EXFOR: https://nucleus.iaea.org/Pages/experimental-nuclear-reaction-data.aspx. This is not a drop-in RSG-GAS core-level detector map.

**Data rule:** do not label published values a reusable raw dataset until the files/tables, units, uncertainty, licensing, benchmark state, and mapping to model observables have been inspected. No external dataset is claimed to have been imported by this change.

## Step 03 — Substantive BRIN relevance

The defensible connection is to Indonesian reactor-neutronics and research-reactor analysis, with RSG-GAS measurements and BRIN-published work as potential evidence sources. CB-PFR's use case is to make candidate-selection decisions auditable: source dataset, model revision, configuration, uncertainty meaning, baseline, and pass/fail reasons.

This is a research/use-case connection, not a claim of BRIN partnership, endorsement, procurement, or deployment.

## Step 04 — CB-PFR and quantum method boundary

CB-PFR remains a post-optimization ranking/selection layer. It does not itself solve neutron transport, create material definitions, or certify reactor safety. The optimization formulation, candidate encoding, solver, simulator/measurement evidence, and ranking method must be separately identified.

The solver taxonomy distinguishes exact classical enumeration, classical heuristics, classical simulated annealing, classical simulated quantum annealing, quantum annealer hardware, and external solvers. The exact solver is a small-instance reference only. The Ocean adapter accepts a sampler supplied by the caller; it does not provision credentials or establish that a QPU ran.

No novel theorem or quantum advantage is claimed. Novelty remains a literature-comparison question.

## Step 05 — Candidate → solver → evaluation → CB-PFR integration

The new `run_solver_to_physics_pipeline(...)` path:
1. Requires solver metadata and verifies solver name/class and variable count against the experiment.
2. Verifies candidate IDs and binary vectors are unchanged from the solver output.
3. Requires one complete evaluation record per candidate; missing, extra, or duplicate records fail closed.
4. Requires metric names, units, and uncertainty semantics to match declared limits.
5. Requires finite means and finite nonnegative uncertainties.
6. Separates synthetic, mock, OpenMC, experimental, and benchmark evidence kinds.
7. Requires an OpenMC statepoint hash, model ID, model revision, and seed for statepoint provenance.
8. Emits formulation identity, solver output, evaluation provenance, ranking rows, non-claims, and a deterministic SHA-256 decision-bundle hash.

### Important C5G7 formulation finding
The current C5G7 QUBO encodes only the constraint of exactly two MOX assemblies. It does not include (k_\mathrm{eff}), fission-rate distribution, or OpenMC response. All six feasible layouts tie in QUBO energy. The valid workflow is to generate/verify candidates, evaluate them under a frozen physics protocol, then rank using declared observables and CB-PFR. A physically superior layout cannot be selected from this QUBO energy alone.

## Validation status

- New tests are committed, but **passing CI has not been observed** through the available status endpoint at the time of writing.
- The local execution container could not reach GitHub to clone and run the tests independently.
- No OpenMC simulation or QPU execution was started by this change.
- No result establishes physical validation, CB-PFR physical superiority, reactor safety, BRIN collaboration, or quantum advantage.

## Next gate

Confirm CI and resolve failures. Then wire the integration contract to archived C5G7 result manifests and dashboard views without rerunning transport. Freeze a higher-budget OpenMC comparison protocol only after the data path and acceptance criteria are reviewed.
