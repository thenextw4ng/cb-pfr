# Phase 1 — Final Software Audit: ReactorQ Studio

**Date:** 2026-10-10  
**Repository:** thenextw4ng/cb-pfr  
**Branch:** integration/reactorq-studio  
**Scope:** source and test review through GitHub, focused on the core QUBO/ranking contracts, dashboard data flow, repeatability analysis, OpenMC preflight/parser, exports, documentation, and CI. No local MacBook environment was accessed.

## Executive result

The software MVP and its tests are implemented on the integration branch. This final audit identified and fixed input-validation gaps in ranking configuration and integration records. The ranking layer now rejects non-finite metric limits/parameters, duplicate metric names, non-finite or negative comparison margins, malformed physical estimate tuples, and arithmetic overflow in calculated bounds. The integration adapter now validates candidate IDs as non-empty strings and rejects estimates for candidates outside the submitted batch. The OpenMC statepoint reader now gives explicit errors for malformed data rather than allowing several malformed-file errors to escape unclassified.

The final CI run for the latest commit must be green before this audit can be called test-verified. GitHub Actions is the execution evidence; this audit does not claim tests ran on the user's machine.

## Reviewed areas

- Package metadata and Python support (pyproject.toml; Python >=3.10).
- QUBO formulation, candidate enumeration, candidate validation, and exact toy-model tests.
- CB-PFR metric configuration, assessment logic, method comparisons, and tie-breaking.
- Candidate-batch integration adapter and provenance-labelled records.
- Streamlit dashboard tabs, state transitions, synthetic labels, error handling, and exports.
- Repeatability library, dashboard JSON input, CLI validation, and output-file no-overwrite behavior.
- OpenMC preflight, stdout keff parsing, statepoint parsing, and explicit no-mapping boundary.
- CI dependency installation, syntax compilation, unit tests, examples, and frozen synthetic benchmark reproduction.

## Findings and remediation

| Finding | Remediation | Remaining limitation |
|---|---|---|
| NaN/infinity could be supplied as metric bounds, scales, weights, or z values. | Reject non-finite/non-numeric parameters and empty metric names. | Scientific appropriateness of user-selected limits still requires justification. |
| Duplicate metric names could collapse into one dictionary key. | Ranking now rejects duplicate metric names. | None for this configuration ambiguity. |
| NaN/infinite uniform margins could pass a simple negative-value check. | Require each margin to be finite, numeric, and nonnegative. | Margin selection remains a methodological choice. |
| Overflow during uncertainty-width or bound arithmetic could produce non-finite intermediate values. | Fail closed with an invalid_width or nonfinite_bound assessment, depending on where overflow occurs. | Extremely large finite inputs are rejected at assessment time. |
| Malformed estimate values could throw instead of producing an explicit failed assessment. | Validate pair shape and numeric types; malformed entries fail closed. | Input provenance is still the caller's responsibility. |
| Candidate IDs were assumed to be strings and stale estimates could be silently ignored. | Require non-empty string IDs and reject estimate IDs outside the candidate batch. | Adapter does not independently prove that a supplied estimate came from a real simulation. |
| Missing assessments could export Infinity values that are not valid strict JSON. | Convert non-finite assessment numbers to JSON null and add a strict JSON serialization regression test. | Null indicates unavailable/invalid assessment values; downstream users must retain status fields. |
| Malformed OpenMC statepoints could leak low-level parsing exceptions. | Wrap expected HDF5/value/type errors in OpenMCIntegrationError; validate keff shape and finite values. | A well-formed statepoint is not proof of converged or physically correct results. |

## Dashboard and reproducibility checks

- The built-in seven-position fixture has 21 binary variables and 20 exactly enumerated feasible candidates; it is clearly described as abstract and not a reactor geometry.
- Demo estimates are deterministic and labelled synthetic. The dashboard does not invent keff, flux, or power tallies.
- The OpenMC panel is a preflight only. It checks executable availability, cross-section path/XML readability, and basic well-formedness of required XML files. It does not launch OpenMC, semantically validate the model, check geometry overlaps, demonstrate convergence, or validate physics.
- Repeatability statistics summarize supplied ordered rankings. They do not launch optimizer runs and do not certify global optimality, physical validity, or statistical confidence.
- The CLI refuses to overwrite an existing output file and records input run IDs and evidence labels.
- CI covers Python 3.10, 3.11, and 3.12; syntax compilation; unit tests; examples; and the frozen synthetic benchmark.

## Scientific evidence boundary and blockers

The repository's mapping audit reports NO_DEFENSIBLE_MAPPING_FOUND. Abstract labels fresh, once_burned, and twice_burned must not be mapped to C5G7 UO2/MOX or any other physical materials without model-specific evidence. Physical validation remains blocked until the benchmark geometry, material/depletion states, category-to-material mapping, nuclear-data provenance, acceptance constraints, and independent reference protocol are documented.

Existing benchmark rates (QUBO-only 0.857, point estimate 0.933, CB-PFR 0.976, uniform margin 0.966) are synthetic conditional results only. They are not reactor simulation outcomes.

## Phase 1 exit checklist

- [x] Review the core source and existing tests relevant to QUBO, ranking, and candidate constraints.
- [x] Review the new integration adapter and provenance labels.
- [x] Review dashboard flow, repeatability input handling, and exports.
- [x] Review OpenMC preflight and parsing boundaries.
- [x] Fix the numeric validation and malformed-input issues listed above.
- [x] Add regression tests for the new guards, including strict JSON export with missing metrics.
- [x] Update documentation with explicit scientific and execution limits.
- [ ] Confirm the latest GitHub Actions workflow passes on Python 3.10, 3.11, and 3.12.

## Exit decision

**Code-review work:** complete.  
**Phase 1 test verification:** pending latest CI result.  
**Physical validation:** blocked / not established.

The next phase should strengthen recorded optimizer-run provenance and prepare the model-specific OpenMC handoff. It must not claim physical evaluation until the mapping and reference gates are resolved.
