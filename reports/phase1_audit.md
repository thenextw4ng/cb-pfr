# Phase 1 Audit — ReactorQ Studio Integration

**Date:** 2026-10-10  
**Repository:** `thenextw4ng/cb-pfr`  
**Integration branch:** `integration/reactorq-studio`  
**Scope:** repository-level audit using GitHub source and CI metadata. No local MacBook environment was accessed.

## Executive summary

CB-PFR is a research prototype for uncertainty-aware post-optimization ranking. It is a suitable foundation for a staged integration, provided the existing method and evidence boundaries are preserved. Phase 1 does not attempt physical simulation, UI implementation, or changes to the CB-PFR algorithm.

## Repository and CI status

- Default branch: `main`.
- A separate integration branch, `integration/reactorq-studio`, was created from `main`.
- The repository's latest visible GitHub Actions run at the time of this audit was completed successfully for commit `cb8580ac714edaaf5e47ad1e64831f486d7b9fc2` (workflow: `.github/workflows/tests.yml`, run 57, recorded 2026-10-05).
- This CI result is evidence that the workflow passed for that commit. It is not evidence that tests were run on the user's local machine or on the new integration branch.
- This audit used the repository metadata and selected source/documentation files through GitHub. It did not execute Python tests itself.

## Existing components found

- Python package metadata is defined in `pyproject.toml`; package name is `cb-pfr`, version `0.1.0`, Python requirement `>=3.10`.
- Existing examples include `examples/toy_qubo_example.py` and `examples/basic_ranking.py`.
- Unit tests are run by `python -m unittest discover -s tests -v`.
- CI covers Python 3.10, 3.11, and 3.12; it compiles source/tests/examples/scripts, runs tests and examples, and reproduces the frozen synthetic benchmark.
- A synthetic benchmark runner and archived trial-level results are documented in `docs/reproducibility.md`.
- The QUBO implementation is an abstract toy model with seven positions, three categories, 21 binary variables, and 20 feasible candidates after exact enumeration, as documented in the repository.
- The OpenMC boundary and QUBO-to-physics mapping audit are designed to fail closed when a defensible mapping is missing.

## Evidence and claims boundary

The repository documents synthetic benchmark selected-feasibility rates of 0.857 (QUBO-only), 0.933 (point estimate), 0.976 (CB-PFR), and 0.966 (uniform margin). These are conditional synthetic results, not reactor simulation outcomes.

The report `reports/qubo_physics_mapping.md` states `NO_DEFENSIBLE_MAPPING_FOUND`. The current abstract categories `fresh`, `once_burned`, and `twice_burned` must not be silently mapped to C5G7 UO2/MOX materials. The physical simulator report also says CB-PFR physical validation has not been established. No OpenMC run was performed as part of this audit.

## Risks and blockers

1. **QUBO-to-physics mapping:** physical evaluation remains blocked until geometry, material/depletion states, category-to-material mapping, nuclear-data provenance, constraints, and an independent validation reference are documented.
2. **Execution environment:** GitHub source inspection does not establish that the user's local environment has the required Python setup or OpenMC installation.
3. **UI versus engine:** ReactorQ Studio should not be built as a static dashboard that invents candidate results. The UI must consume real backend outputs and visibly distinguish demo/mock/synthetic data from actual simulation data.
4. **Algorithm scope:** CB-PFR is a post-optimization ranking layer; it should not be described as a QUBO solver, a reactor safety method, or a global-optimality certificate.

## Phase 1 outcome

**Repository-level audit: COMPLETE.**  
**Local test execution: NOT PERFORMED in this audit.**  
**Physical validation: BLOCKED / NOT ESTABLISHED.**

## Phase 2 plan

1. Define stable data contracts for a QUBO candidate, constraint-check report, run metadata, and downstream evaluation record.
2. Inspect the current QUBO and ranking APIs and add a thin adapter rather than rewriting CB-PFR.
3. Add an integration test using deterministic fixture/synthetic evaluation data, clearly labelled as non-physical.
4. Preserve the current OpenMC fail-closed behavior; only enable physical execution when a documented model and mapping are supplied.
5. Keep the UI out of scope until the backend contracts and end-to-end data flow are tested.
