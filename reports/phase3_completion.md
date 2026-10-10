# Phase 3 — Benchmark selection and physical mapping gate

**Repository:** thenextw4ng/cb-pfr  
**Branch:** stage3/openmc-benchmark-gate  
**Purpose:** establish a cited transport benchmark, formalize the missing mapping evidence, and prevent accidental claims of physical validation.

## Outcome

**Benchmark-selection and software-gate work: implemented. Physical candidate evaluation: blocked.**

The OECD/NEA C5G7 MOX fuel-assembly transport benchmark family is selected as a reference framework for a future OpenMC transport-code verification exercise. The selection is backed by the OECD/NEA benchmark page and specification/reference-analysis report, with OpenMC implementation notes as a secondary implementation reference. The exact benchmark exercise, inputs, and reference quantities still need to be transcribed and independently checked before any baseline run.

The C5G7 fuel categories are not burnup states. The current seven-position QUBO has the abstract categories `fresh`, `once_burned`, and `twice_burned`; the available project evidence does not define their physical compositions, depletion histories, or mapping to physical pin positions. It would be scientifically invalid to relabel these states as UO2/MOX enrichment categories simply because C5G7 is a relevant transport benchmark.

## Completed implementation checklist

- [x] Select and cite a recognized benchmark family for transport-code verification.
- [x] Record benchmark role, source URLs, current implementation state, nonclaims, and mapping contract in a machine-readable manifest.
- [x] Add structural validation for benchmark identity, source citation fields, mapping completeness, input availability, reference data, and baseline verification.
- [x] Fail closed when required evidence is missing; the current manifest reports `blocked`.
- [x] Add a CLI that writes a strict JSON gate report, refuses to overwrite existing output, and exits with code 2 when blocked.
- [x] Add unit and CLI tests covering missing mapping evidence and the no-overwrite behavior.
- [x] Update the QUBO mapping audit and OpenMC handoff checklist.
- [x] Document the benchmark rationale, mapping requirements, and explicit nonclaims.
- [ ] Supply an exact benchmark-specific OpenMC model and compatible nuclear data.
- [ ] Transcribe and review the selected benchmark's exact material compositions, geometry, boundary conditions, reference quantities, and tolerances.
- [ ] Supply a reviewed position-to-geometry and state-to-material/depletion map for the optimizer's candidates.
- [ ] Execute and validate an OpenMC baseline against the chosen benchmark reference.

## Artifacts

- [Benchmark selection dossier](benchmark_selection_c5g7.md)
- [Machine-readable manifest](../config/benchmarks/c5g7_manifest.json)
- [Fail-closed audit implementation](../src/cbpfr/benchmark.py)
- [Audit CLI](../scripts/audit_benchmark_manifest.py)
- [Updated QUBO-to-physics audit](qubo_physics_mapping.md)
- [Updated OpenMC handoff checklist](openmc_handoff_checklist.md)

## Reproduce the gate

```bash
python scripts/audit_benchmark_manifest.py \
  --input config/benchmarks/c5g7_manifest.json \
  --output results/c5g7_benchmark_gate.json
```

Exit code 2 and `status: blocked` are expected with the checked-in manifest. This is a deliberate, correct safety boundary—not a failed test. The audit verifies manifest structure and declared gates; it does not fetch/authenticate source content, verify nuclear-data files, validate an OpenMC model, or establish physical correctness.

## Decision

The Phase 3 *software and source-selection work* is ready for integration. The scientific phase cannot be called physically complete until an actual, defensible mapping exists and a benchmark baseline has been run and checked. No keff, neutron-flux, or power results were generated or invented by this phase.
