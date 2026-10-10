# Phase 3 — Benchmark selection, reproducible source handoff, and physical mapping gate

**Repository:** thenextw4ng/cb-pfr  
**Purpose:** identify a traceable transport benchmark, stage its public implementation reproducibly, and prevent unsupported physical-validation claims.

## Outcome

**Benchmark selection and source-acquisition tooling are implemented. The physical candidate evaluation remains blocked for a scientific reason: the existing QUBO has no defensible physical-state mapping.**

The OECD/NEA C5G7 MOX fuel-assembly transport benchmark is selected as a reference framework. The new [reproducible handoff](c5g7_reproducible_handoff.md) provides a command to clone the public MIT CRPG benchmark implementation and record its exact upstream Git commit in `UPSTREAM_PROVENANCE.json`. This removes the avoidable ambiguity of “which upstream version did we use?” and gives a concrete path to a separately reproducible transport-code exercise.

## What is now supplied

- [x] Cited OECD/NEA benchmark family and specification.
- [x] Machine-readable manifest with explicit scope, mapping contract, and nonclaims.
- [x] Fail-closed manifest validation and CLI.
- [x] Public-source staging script that records the full upstream commit SHA and UTC preparation time.
- [x] Offline tests for refusing to overwrite an existing destination and refusing a missing parent directory.
- [x] A detailed source acquisition, environment, run, uncertainty, and comparison protocol.
- [x] README link and explicit warning that a standalone C5G7 calculation is not CB-PFR candidate validation.

## What is not honestly solvable from the current repository alone

The existing toy QUBO contains seven abstract positions with states `fresh`, `once_burned`, and `twice_burned`. Those labels do not specify isotope inventories, material compositions, burnup, depletion histories, geometry, or a position-to-pin mapping. C5G7's UO2/MOX enrichment categories cannot be substituted for those states without changing the scientific problem.

Therefore, the source-staging helper does **not** mark the benchmark manifest as physically ready, and this report does not claim that a C5G7 model has been executed or validated. A successful independent C5G7 reference run would verify a transport implementation against its own benchmark; it would not prove that CB-PFR correctly ranks the existing QUBO candidates.

To unblock *CB-PFR physical candidate evaluation*, one of these is needed:
1. Original Usmanov-compatible physical model data that define the candidate geometry and each burnup state's material/depletion composition; or
2. A deliberate, documented reformulation of the optimization problem so its decision variables and constraints correspond to a specific benchmark's physical configurations.

Neither can be inferred from the existing code. Choosing one silently would invent the central scientific mapping.

## Reproduce source staging

From the repository root, with Git installed:

```bash
python scripts/prepare_c5g7_reference.py --destination external/mit-crpg-benchmarks
```

The script is deliberately source-only. It does not install OpenMC, obtain all required nuclear data, execute a transport calculation, or compare results with benchmark reference values. Follow [the C5G7 reproducible handoff](c5g7_reproducible_handoff.md) before running the selected case.

The existing manifest audit remains expected to report `blocked` until the input model, cross-section provenance, reviewed reference values, baseline execution, and a valid candidate mapping are supplied. This is an intentional fail-closed result, not a software-test failure.

## Primary sources

- OECD Nuclear Energy Agency, [C5G7 benchmark page](https://www.oecd-nea.org/jcms/pl_13548/benchmark-on-deterministic-transport-calculations-without-spatial-homogenisation).
- OECD/NEA, [C5G7 benchmark specification and reference report](https://www.oecd-nea.org/upload/docs/application/pdf/2019-12/nsc-doc2005-16.pdf).
- MIT Computational Reactor Physics Group, [public benchmark implementation](https://github.com/mit-crpg/benchmarks/tree/master/c5g7/openmc).
- OpenMC, [installation guide](https://docs.openmc.org/en/stable/quickinstall.html).

## Final scientific status

Phase 3's **benchmark-selection, fail-closed software gate, and reproducible source-handoff deliverables** can be considered complete after automated CI passes. **Physical validation of CB-PFR is not complete** and must not be represented as complete until the mapping and baseline evidence above exist.
