# CB-PFR — Confidence-Bounded Physical Feasibility Ranking

> An uncertainty-aware post-optimization selection layer for candidate configurations.

**Author:** Fahry Bagus Adiputra  
**Version:** 0.1.0  
**Status:** research prototype / methodological working paper

## Benchmark protocol

- [Pre-registered candidate-selection benchmark protocol](reports/CB_PFR_PREREGISTERED_SELECTION_BENCHMARK_PROTOCOL_2026-10-11.md): separates method-effect testing from reactor-model validation and defines paired baselines, outcomes, and go/no-go gates.
- [Machine-readable preregistration](config/benchmarks/cbpfr_selection_benchmark_preregistration.json): current status is protocol-only; C5G7 remains exploratory and BEAVRS physical validation is not established.
- [C5G7 same-pool synchronization audit](reports/C5G7_SAME_POOL_CB_PFR_SYNCHRONIZATION_AUDIT_2026-10-11.md): re-computes the current six-layout ranking and explicitly records that CB-PFR did not change the winner versus point-estimate ranking.

## Research question

Optimization can produce candidates that look good under nominal estimates but become fragile when downstream quantities are uncertain. CB-PFR studies whether candidate selection can incorporate uncertainty into the feasibility screen **after** optimization.

CB-PFR is a **post-optimization ranking layer**. It is not a new QUBO optimizer, not a reactor-safety method, and not a claim of physical validation.

## Core mathematics

For candidate i, metric j:

\[
B^-_{i,j}=\hat\mu_{i,j}-z_j\hat s_{i,j},\qquad
B^+_{i,j}=\hat\mu_{i,j}+z_j\hat s_{i,j}.
\]

\[
v_{i,j}=\max(0,L_j-B^-_{i,j})+\max(0,B^+_{i,j}-U_j)
\]

\[
V_{CB}(x_i)=\sum_j w_j\frac{v_{i,j}}{s_j^{scale}}.
\]

The deterministic ranking prioritizes QUBO feasibility, conservative physical feasibility, aggregate violation, QUBO energy, and input order.

**Statistical guardrail:** an arbitrary z multiplier is not automatically a confidence interval. The implementation records uncertainty provenance and defaults to operational-heuristic bounds.

## Evidence status

| Evidence | Status |
|---|---|
| CB-PFR implementation and automated CI | **Present** |
| Abstract QUBO implementation and exact enumeration | **Present** |
| Reduced 1,000-trial synthetic benchmark runner and configuration | **Present** |
| Archived trial-level `results/per_seed_results.csv` | **Included; 4,000 method/trial rows (1,000 trials × 4 methods)** |
| Methodological working paper | **Maintained as a separate publication artifact** |
| MC/DC C5G7 execution evidence | **Recorded execution evidence** |
| CB-PFR physical validation | **Not established** |
| QUBO → C5G7 mapping | **NO_DEFENSIBLE_MAPPING_FOUND** |
| Universal superiority | **Not claimed** |

## Eureka claim-to-evidence matrix

The [claim-to-evidence matrix](reports/EUREKA_CLAIM_EVIDENCE_MATRIX_2026-10-11.md) maps every physical, QUBO, CB-PFR, and quantum claim to required artifacts and states which claims are currently supported, pending, or not established.

## CB-PFR/QUBO integration smoke on C5G7 data

The [C5G7 selection integration report](reports/c5g7_cbpfr_selection_smoke_2026-10-11.md) records a successful code-path test on the archived 18-run corrected-group smoke dataset. The one-hot QUBO enumerated 64 states and selected MUMU under explicitly illustrative screening limits. This is a software integration smoke result only; it is not a benchmark-grade physical winner or evidence of quantum advantage. [Workflow run and artifact](https://github.com/thenextw4ng/cb-pfr/actions/runs/38116610735).

## BEAVRS experimental comparison workflow

A reproducible full-core BEAVRS Cycle 1 day-0 radial detector-map comparison runner and GitHub Actions workflow are now included:

- [BEAVRS comparison protocol](reports/BEAVRS_CYCLE1_EXPERIMENTAL_COMPARISON_PROTOCOL.md)
- [BEAVRS coordinate-registration audit (current mapping still under investigation)](reports/BEAVRS_COORDINATE_REGISTRATION_AUDIT_2026-10-11.md)
- [BEAVRS validation execution plan](reports/BEAVRS_VALIDATION_EXECUTION_PLAN_2026-10-11.md)
- [Run manifest](config/benchmarks/beavrs_validation_manifest.json)
- [Runner script](scripts/run_beavrs_cycle1_map_validation.py)
- [GitHub Actions workflow](.github/workflows/beavrs-cycle1-map-validation.yml)
- [Final 15×15 tilt-corrected BEAVRS run (completed; map validation not established)](https://github.com/thenextw4ng/cb-pfr/actions/runs/38117279412)

The workflow uses the pinned public BEAVRS source, OpenMC 0.15.3, and the official ENDF/B-VII.1 HDF5 data library; it records data hashes and uploads raw run/comparison artifacts. It compares a normalized 58-assembly detector map with mesh-integrated fission rates. A known bank-E insertion mismatch (measurement: 230 steps withdrawn; upstream model default: 228) and the absence of a detector-response/uncertainty-weighted acceptance analysis mean this is an **initial experimental comparison**, not by itself a complete physical-validation certificate. Check the linked workflow run and its artifacts before reporting any numerical result.

## Validation-claim decision

The current defensible claim boundary is recorded in [Validation Claim Decision (2026-10-11)](reports/VALIDATION_CLAIM_DECISION_2026-10-11.md): the method/software has reproducible synthetic-benchmark evidence, while nuclear experimental validation remains **NOT ESTABLISHED**. A KRITZ-2 comparison utility or a successful smoke run is not itself experimental validation.

## Recorded synthetic result

| Method | Selected true-feasibility rate |
|---|---:|
| QUBO-only | 0.857 |
| Point estimate | 0.933 |
| **CB-PFR** | **0.976** |
| Uniform margin | 0.966 |

These are conditional synthetic benchmark results. They are not physical evidence and do not establish universal superiority. Interpret them only under the benchmark's declared data-generating process and protocol.

## Physical-model boundary

The toy model has seven abstract positions, three categorical states (fresh, once_burned, twice_burned), **21 binary variables**, and **20 feasible candidates** after exact enumeration.

The repository deliberately refuses to silently map those labels to C5G7 UO2/MOX material categories. The physical audit records:

`NO_DEFENSIBLE_MAPPING_FOUND`

A future physical study requires documented geometry, material/depletion states, nuclear-data provenance, category-to-material mapping, limits, and an independent validation protocol.

## Evidence archives and local OpenMC baseline

The `main` branch preserves two separate archives:

- `OpenMC_HDF5_Evidence_2026-10-11.zip`: local C5G7/OpenMC HDF5, XML, log, and run metadata supplied for audit.
- `CBPFR_ReactorQ__Archive_2026-10-11.zip`: 86 historical project artifacts recovered from prior conversations and the ChatGPT Library.

Archive integrity is checked in CI with `scripts/audit_evidence_archive.py`. The OpenMC audit workflow reads all four archived statepoints with OpenMC 0.16.0, checks the production keff summary, inventories input hashes/settings, summarizes tally uncertainty, and creates mesh-index plots. A second raw-HDF5 CI check independently reads the production statepoint bytes and passed 10/10 metadata, eigenvalue, mesh-dimension, and score checks on Python 3.10, 3.11, and 3.12 ([workflow](https://github.com/thenextw4ng/cb-pfr/actions/runs/38096943383)). These checks verify extraction and consistency, not benchmark validity or candidate-level physical validation.

Reports: [production statepoint/tally audit](reports/openmc_statepoint_audit_2026-10-11.md), [Stage 3–4 provenance warning](reports/stage34_statepoint_provenance_audit_2026-10-11.md), [remaining-work audit](reports/REMAINING_WORK_AUDIT_2026-10-11.md), [scientific publication-readiness gates](reports/SCIENTIFIC_PUBLICATION_READINESS_GATE_2026-10-11.md), [direct evidence-artifact review](reports/C5G7_EVIDENCE_ARTIFACT_REVIEW_2026-10-11.md), and [independent spatial-mapping audit](reports/C5G7_SPATIAL_MAPPING_AUDIT_2026-10-11.md). The [OpenMC evidence workflow](https://github.com/thenextw4ng/cb-pfr/actions/runs/38084209709) preserves the machine-derived JSON, CSV, settings audit, and six plots as a downloadable artifact.

## ReactorQ Studio and C5G7 layout-study tools

The optional Streamlit dashboard is available with:

```bash
python -m pip install -r requirements-dashboard.txt
streamlit run app.py
```

The built-in demo is synthetic. The “OpenMC preflight” tab checks executable, cross-section path, and XML readability; it does not launch a transport calculation or prove that the physical model is valid.

The separate C5G7 assembly-placement study is available through:
- `scripts/prepare_c5g7_reference.py` — stage public upstream source and record its exact revision.
- `scripts/enumerate_c5g7_layouts.py` — enumerate six two-UO₂/two-MOX placements for the explicit 2×2 design formulation.
- `scripts/run_c5g7_layout_study.py` — prepare isolated cases or run them when a compatible OpenMC installation and nuclear-data setup are available.
- `scripts/audit_c5g7_smoke_statepoints.py` — compare raw HDF5 metadata/scalars with each run manifest and the OpenMC API.
- `scripts/audit_c5g7_evidence.py` — end-to-end integrity gate for six candidates, generated lattice/reflector invariants, settings/seeds, logs, statepoints, all recorded hashes, shared MGXS, and raw-HDF5 audit. The [audit protocol](reports/C5G7_END_TO_END_EVIDENCE_AUDIT_2026-10-11.md) documents the command sequence; adding the gate is not itself a new simulation result.
- `config/benchmarks/c5g7_manifest.json` — fail-closed benchmark/mapping gate.

The assembly-placement formulation is **separate** from the legacy `fresh / once_burned / twice_burned` QUBO. The six isolated input cases have been prepared in CI against pinned upstream commit `ba41bee54320ada0b4ac39a0dd2ca3c1d090a450`; download the [prepared-case artifact](https://github.com/thenextw4ng/cb-pfr/actions/runs/38084994157). The preparation artifact itself did **not** run transport. A separate smoke workflow subsequently completed all six low-budget (100 batches, 10 inactive, 1,000 particles/batch) candidate runs with explicit seeds and recorded statepoint/input hashes. The raw-HDF5 audit passed **112/112 checks** across the six statepoints; see the [raw audit summary](results/c5g7_layout_smoke_2026-10-10/raw_hdf5_audit_summary.json) and [audit workflow](https://github.com/thenextw4ng/cb-pfr/actions/runs/38097364817). See also the [smoke-run analysis](reports/c5g7_smoke_run_2026-10-10.md), [candidate CSV](results/c5g7_layout_smoke_2026-10-10/candidate_summary.csv), and [run manifest](results/c5g7_layout_smoke_2026-10-10/run_manifest.json); full statepoints/logs are in the [workflow artifact](https://github.com/thenextw4ng/cb-pfr/actions/runs/38085586809). These initial six runs are smoke tests, not benchmark-grade ranking. A historical three-round repeatability study completed 18 runs and passed raw-HDF5 checks, but a later audit found that both it and the archived production MGXS used nonstandard log-spaced energy-group boundaries. Those runs are pipeline/provenance evidence only, not standard C5G7 physical validation; the earlier scalar comparison is withdrawn. The runner now uses and audits the standard C5G7 group boundaries before transport. See the [correction record](reports/c5g7_input_provenance_comparison_2026-10-11.md) and [historical smoke evidence note](results/c5g7_repeatability_normalized_2026-10-11/README.md). A corrected-group 18-run smoke study now includes per-seed fission-peaking analysis and variability estimates in the [corrected repeatability report](reports/c5g7_corrected_group_repeatability_smoke_2026-10-11.md); it remains exploratory, and no layout is declared a winner. Historical repeatability CSVs and raw statepoints remain available for provenance review in the [normalized summary](results/c5g7_repeatability_normalized_2026-10-11/repeatability_summary.csv), [run-level hashes](results/c5g7_repeatability_normalized_2026-10-11/run_level_results.csv), and [workflow artifact](https://github.com/thenextw4ng/cb-pfr/actions/runs/38100905238), but they used nonstandard log-spaced energy boundaries and are not standard-C5G7 physical evidence. The old byte-identical MGXS hash and XML path comparison do not validate the group structure. The corrected runner now uses and audits the official C5G7 boundaries before transport. The six layouts are not all official benchmark reference cases; the canonical arrangement is only a baseline identity check. Physical ranking must wait for corrected runs, reviewed model/material correspondence, repeated runs per layout, and a predeclared acceptance protocol. The current archived Stage 3–4 statepoints are not valid independent-seed repetitions; see [the provenance audit](reports/stage34_statepoint_provenance_audit_2026-10-11.md).

The corrected-group 18-run results now have an additional machine-checked evidence audit: `scripts/audit_c5g7_corrected_objective.py` checks all six layouts, three runs per layout, unique seeds/statepoints, common corrected MGXS identity, and standard-group audits; it computes descriptive Student-t intervals but **intentionally refuses to declare a winner** until a design-specific k_eff band and independent tally review exist. See [three-gate execution status](reports/c5g7_three_gates_execution_status.md) and [the audit script](scripts/audit_c5g7_corrected_objective.py).

For a precise but separate optimization encoding, `src/cbpfr/c5g7_design_qubo.py` represents the four UO2/MOX assembly choices with binary variables and the exact-two-MOX penalty `A(sum(y)-2)^2`. It enumerates exactly the same six feasible layouts and does **not** pretend that the legacy burnup-state QUBO maps to C5G7. The staged screening protocol is in `config/benchmarks/c5g7_validation_protocol.json`, the audit CLI is `scripts/audit_c5g7_validation_gates.py`, and the decision record is [C5G7 validation and mapping plan](reports/C5G7_VALIDATION_AND_MAPPING_PLAN.md). The proposed 2,000/100/5,000 run profile is being evaluated by a separate long-running workflow and is not automatically benchmark-grade. See the [production-versus-canonical input comparison](reports/c5g7_input_provenance_comparison_2026-10-11.md), [validation/mapping plan](reports/C5G7_VALIDATION_AND_MAPPING_PLAN.md), and [smoke validation gate audit](results/c5g7_smoke_validation_gate_audit_2026-10-11.json), plus the [six-layout fission-rate proxy report](reports/c5g7_assembly_fission_proxy_smoke_2026-10-11.md).

## Repository architecture

    cb-pfr/
    ├── README.md
    ├── CITATION.cff
    ├── .zenodo.json
    ├── requirements.txt
    ├── LICENSE-CODE.txt
    ├── LICENSE-PAPER.txt
    ├── src/cbpfr/
    ├── config/
    ├── results/
    ├── reports/
    ├── examples/
    ├── tests/
    ├── scripts/
    └── .github/workflows/tests.yml

The methodological working paper is maintained as a separate publication artifact so that the software release remains a clean code/data archive.

## Quick start

The core package uses the Python standard library.

    git clone https://github.com/thenextw4ng/cb-pfr.git
    cd cb-pfr
    python -m venv .venv
    . .venv/bin/activate
    pip install -e .
    python examples/toy_qubo_example.py
    python examples/basic_ranking.py
    python -m unittest discover -s tests -v

## Reproduce the reduced synthetic benchmark

Use a new output directory (the runner refuses to overwrite a nonempty one):

    python scripts/run_reduced_synthetic_calibration.py --results-dir results/reproduced_run

This generates fresh trial-level output and aggregate/audit files from the checked-in code and configuration. The preserved archival `results/per_seed_results.csv` is provided for direct row-level comparison.

The benchmark has already been independently re-executed from the released source and frozen configuration. All substantive trial-level fields in the regenerated 4,000-row output matched the archival CSV, and the four aggregate selected-feasibility rates matched exactly. This is an **independent computational rerun**, not an external third-party replication.

See [docs/reproducibility.md](docs/reproducibility.md), [docs/limitations.md](docs/limitations.md), and [FINAL_RELEASE_AUDIT.md](FINAL_RELEASE_AUDIT.md) for the evidence boundary.

## Design principles

- **Fail closed:** missing/invalid uncertainty does not silently pass.
- **Deterministic:** ranking and tie-breaking are explicit.
- **Auditable:** evidence provenance is separated from claims.
- **No invented physics:** abstract categories are not silently mapped to materials.
- **Reusable:** the method is separated from the manuscript.

## Citation

Use [CITATION.cff](CITATION.cff) for repository metadata and cite the working paper for methodological discussion. The repository release DOI will be added here after the `v0.1.0` GitHub release is archived by Zenodo.

## License

Code: MIT.  
Paper/documentation: CC BY 4.0.


## Usmanov 2024 optimization benchmark and quantum-claim gate

The repository now records the seven published core-size instances from Usmanov et al. (2024) in `config/benchmarks/usmanov_2024_core_instances.csv` and provides a repeated-trial TTS analyzer in `scripts/analyze_solver_benchmark.py`. The reproduction protocol and claim boundary are documented in [reports/USMANOV_2024_REPRODUCTION_AND_QUANTUM_CLAIM_GATE.md](reports/USMANOV_2024_REPRODUCTION_AND_QUANTUM_CLAIM_GATE.md).

This is benchmark infrastructure, not a completed independent reproduction. The published paper's aggregate figure is not raw per-trial quantum-device data. No new D-Wave job or quantum-advantage result is claimed. Run-level results must be collected on the same instances and success criterion, with setup/embedding and end-to-end costs reported separately. The paper itself reports that practical advantage had not yet been reached.

An optional [D-Wave QPU runner](scripts/run_dwave_qubo_benchmark.py) now accepts a frozen QUBO JSON, records repeated sampler calls and their returned samples, and writes audit metadata. It requires an independently configured `DWAVE_API_TOKEN` and the optional `dwave-system` package; this repository has **not** submitted a QPU job. Its energy-threshold success flag is not a physical-feasibility claim. See the [Usmanov reproduction and quantum-claim gate](reports/USMANOV_2024_REPRODUCTION_AND_QUANTUM_CLAIM_GATE.md).


## External QUBO benchmark comparison (public recorded data)

A public external comparison has been transcribed by family, with a pinned upstream source revision and explicit evidence limitations:
- [External benchmark evidence report](reports/PUBLIC_QUBO_BENCHMARK_EXTERNAL_EVIDENCE.md)
- [Machine-readable aggregate CSV](config/benchmarks/public_qubo_benchmark_summary.csv)

The upstream summary covers 1,912 QUBO instances: the classical reference has a lower objective on 1,280 matched cases, equal objective on 576, and 56 cases lack a D-Wave result. This is **source-reported aggregate evidence, not an independent rerun**, not a nuclear fuel-management dataset, and not evidence that CB-PFR improves QPU outputs. No QPU job was submitted by this repository.


### Physical-validation gate reports

- [BEAVRS experimental comparison protocol and latest result](reports/BEAVRS_CYCLE1_EXPERIMENTAL_COMPARISON_PROTOCOL.md) — current map mismatch and temperature-matched rerun status.
- [C5G7 CB-PFR physical-effectiveness gate](reports/C5G7_CB_PFR_PHYSICAL_EFFECTIVENESS_GATE_2026-10-11.md) — descriptive six-layout results, canonical (k_\mathrm{eff}) uncertainty check, and why the smoke study does not yet demonstrate a CB-PFR treatment effect.
- [Validation claim decision](reports/VALIDATION_CLAIM_DECISION_2026-10-11.md) — supported and unsupported claims.

These reports intentionally separate software/integration evidence from nuclear benchmark validation and physical selection effectiveness.
