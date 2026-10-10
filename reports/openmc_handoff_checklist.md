# OpenMC handoff checklist — do not run until model mapping is defensible

This checklist separates software readiness from physical-model validity. ReactorQ Studio currently performs preflight checks only. It does not construct an OpenMC model or launch a transport calculation.

## Gate 0 — select a defensible model

- [x] Select and cite the OECD/NEA C5G7 benchmark family as a *transport-code reference framework* in [benchmark selection dossier](benchmark_selection_c5g7.md); the machine-readable manifest is `config/benchmarks/c5g7_manifest.json`.
- [x] Add a fail-closed manifest audit (`scripts/audit_benchmark_manifest.py`) that records missing model/mapping/reference evidence rather than treating it as success.
- [ ] Instantiate one exact C5G7 exercise and identify the exact benchmark or reactor model configuration to reproduce.
- [ ] Record the benchmark's intended scope, geometry, materials, boundary conditions, and reported reference quantities.
- [ ] Verify that the model's geometry and material categories can be represented by the candidate configurations being evaluated.
- [ ] Document the mapping from each optimizer category to an actual material/composition/depletion state. If this mapping is not supported by source evidence, stop.
- [ ] Do not equate the repository's abstract fresh, once_burned, and twice_burned labels with UO2/MOX or any other real material without a documented model-specific basis.
- [ ] Record nuclear-data library name, version, path, and provenance; confirm compatibility with the selected benchmark.

**Stop condition:** the benchmark family selection is complete, but the physical model is not instantiated and category-to-material mapping remains unresolved. If category-to-material mapping, geometry mapping, or benchmark provenance is unresolved, do not report any OpenMC result as a CB-PFR physical validation.

## Gate 1 — prepare and validate input files

Required XML files expected by the current preflight:
- [ ] materials.xml
- [ ] geometry.xml
- [ ] settings.xml

Also verify:
- [ ] OpenMC executable is installed and its version is recorded.
- [ ] OPENMC_CROSS_SECTIONS points to the intended cross-section index.
- [ ] XML files parse and geometry checks pass for the selected OpenMC version.
- [ ] Particle histories, inactive batches, active batches, and random seed are documented.
- [ ] The model has a declared source/reference protocol and acceptance tolerances before results are inspected.

Preflight success only means that expected runtime and files appear available. It does not prove correct geometry, physical fidelity, convergence, or validation.

## Gate 2 — establish a reference calculation

- [ ] Run the unmodified reference configuration first.
- [ ] Preserve stdout/stderr, input files, OpenMC version, cross-section provenance, random seed, and runtime metadata.
- [ ] Inspect convergence diagnostics and the reported uncertainty for k-effective.
- [ ] Define required tallies before execution (for example, neutron flux or fission/power-related quantities only if the model and tally definitions support them).
- [ ] Compare reference outputs against a cited benchmark using predeclared tolerances.
- [ ] If the reference calculation fails validation, stop before evaluating optimizer-selected candidates.

## Gate 3 — evaluate candidate configurations

- [ ] Generate each candidate from a documented and deterministic mapping to the validated model.
- [ ] Check categorical and physical constraints before writing OpenMC inputs.
- [ ] Give every candidate and run a stable ID; save the exact generated inputs.
- [ ] Use a documented seed strategy and sufficient histories/batches for the required precision.
- [ ] Parse results only when the run completed successfully and the required output fields are present.
- [ ] Preserve raw outputs and uncertainties; do not substitute missing metrics with zeros.
- [ ] Mark failed, nonconverged, or incomplete runs explicitly instead of silently excluding them.

## Gate 4 — repeated-run and CB-PFR analysis

- [ ] Define whether repeated runs vary optimizer seeds, Monte Carlo seeds, or both. Analyze these sources of variability separately when possible.
- [ ] Save optimizer name/version, solver settings, seed, stopping criterion, candidate IDs, QUBO energy, feasibility status, and runtime.
- [ ] Save physical metrics, units, reported uncertainties, tally definitions, run status, and input/model hashes.
- [ ] Compute repeatability statistics from actual recorded independent runs; the dashboard's default sample data is illustrative only.
- [ ] State that selection frequency is descriptive and is not a global-optimum certificate.
- [ ] Report CB-PFR as a candidate-selection method, not a reactor-safety certification.

## Deliverables for the handoff

1. Benchmark/source citation and mapping rationale ([benchmark-selection dossier](benchmark_selection_c5g7.md) completed; physical mapping still blocked).
2. Versioned OpenMC input files and nuclear-data provenance record.
3. Baseline run log and reference-comparison report.
4. Candidate manifest linking each optimizer candidate to exact physical inputs.
5. Raw outputs, parsed metrics, uncertainty fields, and failed-run records.
6. Reproducible repeated-run summary and a clear limitations statement.
