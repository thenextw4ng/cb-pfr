# Step 01–05 implementation and evidence audit
**Date:** 2026-10-12  
**Repository:** `thenextw4ng/cb-pfr`  
**Working branch:** `feature/step05-scientific-integration`  
**Scope:** repository audit, evidence/data-source plan, BRIN relevance, CB-PFR method boundary, and candidate-to-evaluation integration contract.

## Executive outcome

Steps 01–05 have been advanced on an isolated branch. The main branch is untouched. The new integration layer is a software contract, not a claim that OpenMC was executed or that CB-PFR has physical validation.

### Changes made
- Added `src/cbpfr/experiment.py`: versioned experiment metadata, candidate evaluation records, metric observations with units and uncertainty semantics, provenance validation, fail-closed candidate/evaluation matching, single-source-kind comparisons, ranking orchestration, and deterministic bundle SHA-256.
- Added `tests/test_experiment_contract.py`: tests for versioned output, source provenance, explicit OpenMC metadata, missing/duplicate candidates, mixed data sources, units and uncertainty semantics, ambiguous units, and stable bundle hashing.
- Exported the contract from `cbpfr` and advanced package version to `0.2.0`.
- Preserved all existing QUBO formulations and OpenMC runners. No direct mapping from the legacy burnup-state QUBO to C5G7 UO₂/MOX has been introduced.
- Added this execution report as an audit trail.

## Step 01 — Repository and claim audit

### Existing architecture found
- `src/cbpfr/qubo.py`: categorical burnup-state QUBO with fresh / once-burned / twice-burned labels and constraint penalties.
- `src/cbpfr/c5g7_design_qubo.py`: separate four-position C5G7 UO₂/MOX placement encoding with exactly two MOX assemblies; six feasible layouts.
- `src/cbpfr/ranking.py`: CB-PFR conservative feasibility ranking and point-estimate / uniform-margin / QUBO-only comparators.
- `src/cbpfr/integration.py`: prior thin adapter from QUBO candidates and physical estimates to rankings and JSON/CSV-like records.
- `src/cbpfr/openmc.py`: OpenMC preflight, candidate manifest and statepoint/keff parsing helpers. It deliberately refuses to infer materials or geometry from burnup labels.
- Existing CI runs unit tests, source compilation, archive audits, and synthetic reproduction checks.

### Evidence constraints that remain binding
1. The 40,000-pool confirmatory synthetic study did not reach its predeclared practical-effect threshold of +2 percentage points. It is not evidence of general or physical superiority.
2. The archived C5G7 18-statepoint selection smoke demonstrates pipeline operation under illustrative limits, not benchmark-grade physical validation. CB-PFR and the point-estimate baseline selected the same layout in the recorded comparison.
3. The BEAVRS experimental spatial-map comparison had poor spatial agreement and is not successful physical validation.
4. The legacy burnup-state QUBO and C5G7 material-placement QUBO are different formulations. No material/depletion mapping was silently added.
5. Exact enumeration and classical simulated quantum annealing are not quantum-device execution and do not establish quantum advantage.

## Step 02 — Dataset and evidence-source plan

The integration contract distinguishes these source kinds:
- `synthetic`: generated from a declared data-generating process.
- `mock`: illustrative UI/test fixture only.
- `openmc_statepoint`: output tied to a statepoint hash, explicit model identity/revision, and seed.
- `experimental_measurement`: measured data with an identifiable source reference and measurement uncertainty definition.
- `benchmark_reference`: reference values for a declared benchmark, kept distinct from new simulator output.

### Candidate sources to audit before use
- Existing repository C5G7/OpenMC statepoints and manifests: immediately available for provenance/integrity work; currently exploratory evidence.
- BEAVRS Cycle 1 day-0 experimental detector map and pinned upstream model: available in the repository's workflow and analysis artifacts; current spatial agreement is poor, so do not use as a validation success.
- BRIN's *Atom Indonesia* paper on neutron-flux measurement at RSG-GAS with foil-activation benchmarking: `https://atomindonesia.brin.go.id/index.php/aij/article/view/1768`. This is a source lead, **not** confirmation that all raw measurements are downloadable or compatible with the current model.
- IAEA research-reactor computational benchmarking report: `https://www-pub.iaea.org/MTCD/Publications/PDF/TE-1879_web.pdf`. Use only after checking the benchmark state, observables, data access, and acceptance criteria.
- IAEA EXFOR experimental reaction data: `https://nucleus.iaea.org/Pages/experimental-nuclear-reaction-data.aspx`. It is a possible source for nuclear reaction-data work, not a drop-in RSG-GAS core-level detector map.

**Data rule:** do not label a paper's reported values as a reusable raw dataset until the underlying table/files, units, uncertainty, licensing, benchmark state, and mapping to model observables have been inspected. No external dataset is claimed to have been imported by this commit.

## Step 03 — Substantive BRIN relevance

The defensible product connection is to Indonesian reactor-neutronics and research-reactor analysis, with RSG-GAS measurements and BRIN-published work as potential evidence sources. The product's use case is to make candidate-selection decisions auditable: each result should expose the source dataset, model revision, configuration, uncertainty meaning, comparison baseline, and reason a candidate passed or failed a declared screen.

This is a research/use-case connection, **not** a claim of BRIN partnership, endorsement, procurement, or deployment. Formal collaboration requires direct contact and confirmation.

## Step 04 — CB-PFR method boundary

CB-PFR remains a post-optimization ranking/selection layer. It does not itself solve QUBO, run neutron transport, create material definitions, or certify reactor safety. The optimization formulation, candidate encoding, simulator/measurement evidence, and ranking method must be separately identified.

The new `ExperimentSpec` requires explicit:
- `formulation_id` — the mathematical problem/encoding family used;
- `candidate_encoding_id` — how candidate vectors map to named candidate states;
- `optimizer_name` and `optimizer_class` — including a distinction between classical simulated quantum annealing and a quantum annealer;
- `code_revision` — the code revision associated with the experiment.

The contract deliberately does not claim a novel theoretical theorem. Novelty remains a literature-comparison question; current evidence supports describing CB-PFR as the user's proposed and implemented method, with synthetic results interpreted only under their declared protocol.

## Step 05 — Candidate → evaluation → CB-PFR integration

The new `run_ranked_experiment(...)` path now enforces:
1. Every candidate has a non-empty unique ID.
2. Every candidate has exactly one evaluation record; missing, extra, or duplicate records fail closed.
3. Every evaluation contains exactly the metrics declared by the experiment.
4. Each observation includes a finite mean, nonnegative finite uncertainty, explicit units, and explicit uncertainty semantics.
5. Observation units and uncertainty kind must match the declared metric limits.
6. One comparison batch cannot silently mix synthetic, mock, OpenMC, experimental, and benchmark-reference records.
7. OpenMC statepoint provenance requires a SHA-256, model ID, model revision, and explicit seed.
8. Output has a versioned schema marker, formulation identity, source classification, per-candidate provenance, ranking rows, and explicit non-claims.
9. A stable JSON serialization can be hashed for a bundle-level integrity identifier.

### Why this matters
The old adapter accepted a map of estimates but did not establish a versioned, per-candidate evidence contract. The new boundary is designed to prevent a synthetic demo from being accidentally presented as OpenMC output, prevent incomplete candidate batches from receiving a ranking, and preserve the identity of the formulation. It still cannot prove that an input model is physically correct or that its limits are scientifically justified.

## Validation status

- New tests are committed in `tests/test_experiment_contract.py`; GitHub Actions must be checked for the resulting commit before calling them passed.
- The contract does not launch OpenMC. Long transport runs are deferred until a specific protocol, source/model revision, tally observable, acceptance rule, and compute budget are frozen.
- No result in this report establishes physical validation, an incremental physical benefit from CB-PFR, reactor safety, BRIN collaboration, quantum-device execution, or quantum advantage.

## Immediate next gate

Run CI on this branch and resolve any failures. Then wire the contract into the existing C5G7 result loader and dashboard using archived result manifests without rerunning transport. Only after that data path passes should we freeze a higher-budget OpenMC comparison protocol.
