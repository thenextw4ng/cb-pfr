# ReactorQ Studio implementation audit

**Audit date:** 2026-10-11  
**Repository:** `thenextw4ng/cb-pfr`  
**Audited revision:** `1907b2babb250923a73e06f67a51842d561d20e3`  
**Working branch for follow-up:** `research/reactorq-finalization-20261011`

## Executive finding

This repository is a research prototype containing an abstract categorical QUBO, a separate four-position C5G7 UO2/MOX layout encoding, CB-PFR ranking, OpenMC run scripts, evidence audits, a small dashboard, and archived synthetic results. The components are not yet one scientifically justified end-to-end optimizer-to-reactor pipeline. The repository explicitly reports `NO_DEFENSIBLE_MAPPING_FOUND` for the legacy burnup-state QUBO to C5G7 material mapping; this audit preserves that fail-closed status.

## Initial evidence checked

- GitHub Actions run [38112118549](https://github.com/thenextw4ng/cb-pfr/actions/runs/38112118549), commit above, completed successfully. The job installed OpenMC 0.16.0, checked out pinned MIT-CRPG benchmark source commit `ba41bee54320ada0b4ac39a0dd2ca3c1d090a450`, generated the model and ran a new statepoint calculation.
- Raw-HDF5 audit returned 22 passed checks and zero failed checks.
- The one-run assembly report gives (k_{eff}=1.1728029349), reported within-run standard deviation (0.0194723237), and assembly-integrated fission-rate peaking factor (1.9429328428).
- The statepoint is from 20 total batches, 5 inactive, 100 particles per batch: only 15 active batches and 1,500 active particle histories by the nominal setting. This is a smoke test, not a convergence study.
- Artifact ZIP SHA-256 reported by GitHub: `76999d475adde0f98d045293a72521898933334a162679b51dd74ad682b1fa23`. The artifact preserves 34 files including input XML, logs, statepoint, summary, manifest, and analysis.
- The output explicitly reports `all_runs_completed_needs_independent_validation`; the existing fission-analysis script explicitly says uncertainty is not propagated for correlated mesh bins.
- `examples/c5g7_published_reference_baseline.csv` stores (k_{eff}=1.18655pm0.000095) and a value 2.498 in a column named `fission_rate_peaking_factor`. The cited paper labels 2.498 as *maximum pin power*, not assembly-integrated fission-rate peaking factor. This is a schema/semantic mismatch; do not compare those two metrics numerically.
- The benchmark manifest records the historical nonstandard `np.logspace(-5, 7, 8)` group edges as a prior issue and requires standard C5G7 group boundaries plus primary-specification review. The quick-check runner now patches the boundaries, but independent full model-identity review is still outstanding.

## Component map

| Component | Responsibility | Audit status |
|---|---|---|
| `src/cbpfr/qubo.py` | Abstract 3-state burnup categories, upper-triangular QUBO, exact enumeration and feasibility | Software implementation present; no approved C5G7 material mapping |
| `src/cbpfr/c5g7_design_qubo.py` | Separate 4-bit, exactly-two-MOX encoding and six-layout enumeration | Exact cardinality formulation is present; does not by itself evaluate physics |
| `src/cbpfr/ranking.py` | CB-PFR bounds and deterministic candidate ranking | Operational heuristic is documented; input uncertainty must be justified externally |
| `scripts/run_c5g7_layout_study.py` | Pinned upstream C5G7 source preparation, model patching, transport runs and manifests | Real OpenMC run evidenced; full convergence/model review not passed |
| `scripts/analyze_c5g7_assembly_fission.py` | Integrates 51x51 fission mesh into four assembly blocks and computes a ratio | Metric computed; per-statepoint mesh covariance not propagated |
| `scripts/audit_c5g7_mapping_contract.py` | Fail-closed provenance contract | Correctly refuses to certify physical mapping |
| `scripts/aggregate_c5g7_fission_replicates.py` | New between-seed aggregation of per-run nonlinear metrics | Added with tests; CI execution must confirm |
| `scripts/compare_c5g7_reference.py` | New metric-aware comparison with one published canonical reference | Added with tests; intentionally blocks unlike power observables |
| `app.py` / `docs/api.md` | Dashboard and public research API | Suitable for a research UI prototype, not a certified reactor-design interface |

## Requirement status at audit time

- QUBO algebra and exact cardinality: **implemented**, with automated tests; physical interpretation is a separate question.
- One canonical OpenMC transport smoke run: **PASS** for execution and technical statepoint checks only.
- Benchmark reproduction: **NOT ESTABLISHED**; the quick-check budget is too small and G0 model identity review is still blocked.
- Independent numerical comparison: **partial/screening only** for (k_{eff}); no acceptance claim.
- Independent assembly/pin power comparison: **BLOCKED** because the available published value is a different observable.
- Independent-seed uncertainty for nonlinear peaking factor: new aggregation path implemented; requires distinct-seed production runs before a project result exists.
- QUBO-to-physical mapping: **BLOCKED** until material-state semantics and independent review are supplied.
- Experimental physical validation: **NOT ESTABLISHED**; C5G7 is a computational benchmark, not experimental data for this project.

## Non-destructive policy

Historical result archives and the previous successful run are retained. New outputs must use fresh paths. Numerical mismatches are recorded as evidence and not edited away. Green CI is not a validation certificate.


## Follow-up: three-seed corrected-group smoke run

A second real OpenMC workflow, [run 38112597526](https://github.com/thenextw4ng/cb-pfr/actions/runs/38112597526), completed successfully after the audit commit. It ran 18 cases (six layouts × three seed rounds), with 100 batches, 10 inactive batches, and 1,000 particles per batch. All standard C5G7 group-structure audits passed, statepoint hashes were unique, the generated lattice matched the layout signatures, and all runs shared corrected MGXS SHA-256 `a4328a7b012321fbe8f661745aa135f0a2eecd34cf475429e160865204acb129`. The artifact digest is `sha256:60a08ec9907a7344e40c1d9e7800800de9dd71d83ecb7e072b8106775ed567bc`.

For canonical UMMU, the three-run mean was (k_{eff}=1.18610263), between-seed SD (0.00386340), and derived assembly peaking mean (1.886113) with between-seed SD (0.028995). These are descriptive smoke-budget estimates, not calibrated confidence intervals. The run still reports `EXPLORATORY_DESCRIPTIVE_ONLY`; it does not resolve model identity or the missing burnup-QUBO material mapping.
