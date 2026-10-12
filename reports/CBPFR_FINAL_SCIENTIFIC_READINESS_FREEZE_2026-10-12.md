# CB-PFR Final Scientific Readiness Freeze

**Decision date:** 2026-10-12  
**Scope:** CB-PFR / ReactorQ Studio C5G7 four-fuel-position placement study  
**Status:** ACCEPTANCE CONTRACT FROZEN; FINAL RELEASE NOT YET APPROVED

## 1. Non-negotiable scope freeze

The project scope is frozen. Do not add new algorithms, metrics, experiments, or cosmetic refactors after this contract is accepted, except when needed to fix a reproducible defect, a failing test, a scientific-validity issue, or an explicit submission requirement. Do not modify the active canonical simulation model/settings without recording a new version and input hashes.

The study covers six layouts over four fuel positions with exactly two UO2 and two MOX assemblies; five reflector positions remain fixed. This is a placement reformulation and must not be described as a reproduction of the legacy Usmanov burnup-state QUBO.

No QPU requirement, BEAVRS validation requirement, reactor-safety certification, quantum-advantage claim, or absolute-power claim is added to this finish line.

## 2. Definition of done

A deliverable may be called complete only when its acceptance evidence is recorded. Keep these statuses separate:

- **Software-ready:** application and analysis pipeline execute; automated tests pass; malformed/incomplete evidence fails closed; outputs and provenance are traceable; usage and reproduction instructions exist.
- **Research-ready:** final analysis, figures, tables, methods, uncertainty treatment, limitations, and manuscript agree with the recorded evidence.
- **Physics-validated:** only the specific validation claim supported by an appropriate trusted reference, verified tally mapping, and uncertainty-aware comparison may be made. Completion of an OpenMC run alone does not establish physical validation.

## 3. A–G acceptance gates

### A — Model identity and provenance
- Record upstream repository and pinned commit, OpenMC version, generated geometry/material/settings/source inputs, MGXS identity/hash and group boundaries, boundary conditions, run settings, command, environment, and output hashes.
- Verify the actual generated inputs used by each production run, not only a template or source-code expectation.
- Document physically meaningful differences between smoke-test and production configurations.
- A matching hash establishes identity, not fidelity. Record the model-specification review status.
- **Pass evidence:** complete manifest tied to the exact run artifacts and documented review. Missing or mismatched provenance fails closed.

### B — Mesh-to-assembly mapping
- Preserve unit tests for array shape, block indexing, arithmetic, material order, excluded reflector bins, non-finite/negative values, invalid material count, and zero-rate blocks.
- Verify mesh bounds, bin ordering, lattice orientation, fuel boundaries, and tally filter semantics against the actual generated geometry and OpenMC statepoint.
- Define score units and normalization. A summed fission tally is a fission-rate proxy unless a separate normalization and interpretation justify another term; do not call it absolute power.
- Compare compatible spatial quantities with a trusted, benchmark-compatible reference before claiming spatial validation.
- **Pass evidence:** test results plus a documented mapping audit grounded in actual run inputs/output and reference compatibility.

### C — QUBO and design-space correctness
- Exhaustively enumerate all six permitted layouts and verify exactly two UO2, two MOX, and fixed reflector positions.
- Cross-check QUBO energy and constraint feasibility against direct calculation for every layout.
- Reject malformed vectors and inconsistent solver metadata.
- Do not select a winner unless the physical objective and acceptance criteria are justified and predeclared.
- **Pass evidence:** reproducible enumeration report and passing tests for all six layouts.

### D — Data integrity and reproducibility
- Verify every expected seed has its matching statepoint and summary, unique artifact hashes where expected, shared MGXS/group structure, consistent settings, required fields, and intact outputs.
- Preserve exact commit, input hashes, environment, commands, logs, statepoints, and analysis outputs.
- Distinct hashes alone do not prove independent physics or correct model identity.
- **Pass evidence:** automated audit report tied to all expected run artifacts; missing, duplicate, or corrupt evidence cannot be treated as a pass.

### E — Physical metrics and benchmark protocol
- State definitions, units, normalization, uncertainty handling, comparison metric, exclusions, and pass/fail/inconclusive logic before interpreting final results.
- Keep project screening thresholds distinct from official benchmark acceptance criteria.
- Report per-run tally uncertainty and between-seed variability; state assumptions behind reference differences and combined z-scores.
- **Pass evidence:** an auditable metric protocol and results compared only to a compatible, identified reference. No unsupported winner or physical-validation claim.

### F — CI and fail-closed integration
- Run the test matrix on the exact final commit.
- Test invalid QUBO inputs, malformed/missing evidence, inconsistent settings, absent diagnostics, and ranking when the physical objective is not approved.
- **Pass evidence:** all required CI checks green on the exact commit proposed for release, with the SHA recorded. CI success is software evidence, not physics validation.

### G — Analysis, reporting, and release
- Produce per-run results, uncertainty, between-seed sample SD, reference differences and stated comparison assumptions, convergence diagnostics, spatial metric and uncertainty where valid, provenance, and explicit limitations.
- Finalize UI labels, tables, figures, methods, conclusions, documentation, and reproduction instructions from actual evidence.
- **Pass evidence:** release checklist complete; manuscript and software outputs agree; unresolved items are explicitly bounded and do not support affirmative claims.

## 4. Run-dependent closing procedure

When the canonical high-budget UMMU confirmation run is available:

1. Verify all expected seed artifacts, logs, statepoints, hashes, and exact model/settings identity.
2. Run the frozen audit and analysis pipeline once on the complete evidence set.
3. Evaluate uncertainty, convergence, reference comparison, and each predeclared screen without changing thresholds after seeing the outcome.
4. If a gate fails, diagnose only the concrete failure. Repeat a run only if the failure is technical or a documented evidence gap makes the result uninterpretable. Do not repeat solely to obtain a preferred outcome.
5. Freeze figures, tables, conclusions, paper, and release package if all required gates are closed or the remaining scientific limits are explicitly bounded.

## 5. Stop rule

After the definition of done is met, stop scope expansion. No new method, metric, experiment, algorithm, or cosmetic redesign unless it fixes a documented defect, closes a required acceptance gate, or satisfies an explicit submission requirement.

A scientifically negative or inconclusive result can still be reported honestly. Do not relabel a failed screen as a pass, and do not claim reactor safety, absolute power validation, a winning layout, or quantum advantage without the necessary evidence.

## 6. Status at freeze

This document freezes acceptance criteria; it does not assert that all gates have passed. The canonical high-budget confirmation, final model-identity review, actual statepoint mapping verification, convergence interpretation, and benchmark-compatible spatial validation remain run-/evidence-dependent until their specific artifacts and reviews are recorded.
