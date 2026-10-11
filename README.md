# CB-PFR — Confidence-Bounded Physical Feasibility Ranking

> An uncertainty-aware post-optimization selection layer for candidate configurations.

**Author:** Fachry Bagus Adiputra  
**Version:** 0.1.0  
**Status:** research prototype / methodological working paper

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

Reports: [production statepoint/tally audit](reports/openmc_statepoint_audit_2026-10-11.md), [Stage 3–4 provenance warning](reports/stage34_statepoint_provenance_audit_2026-10-11.md), and [remaining-work audit](reports/REMAINING_WORK_AUDIT_2026-10-11.md). The [OpenMC evidence workflow](https://github.com/thenextw4ng/cb-pfr/actions/runs/38084209709) preserves the machine-derived JSON, CSV, settings audit, and six plots as a downloadable artifact.

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
- `config/benchmarks/c5g7_manifest.json` — fail-closed benchmark/mapping gate.

The assembly-placement formulation is **separate** from the legacy `fresh / once_burned / twice_burned` QUBO. The six isolated input cases have been prepared in CI against pinned upstream commit `ba41bee54320ada0b4ac39a0dd2ca3c1d090a450`; download the [prepared-case artifact](https://github.com/thenextw4ng/cb-pfr/actions/runs/38084994157). The preparation artifact itself did **not** run transport. A separate smoke workflow subsequently completed all six low-budget (100 batches, 10 inactive, 1,000 particles/batch) candidate runs with explicit seeds and recorded statepoint/input hashes. The raw-HDF5 audit passed **112/112 checks** across the six statepoints; see the [raw audit summary](results/c5g7_layout_smoke_2026-10-10/raw_hdf5_audit_summary.json) and [audit workflow](https://github.com/thenextw4ng/cb-pfr/actions/runs/38097364817). See also the [smoke-run analysis](reports/c5g7_smoke_run_2026-10-10.md), [candidate CSV](results/c5g7_layout_smoke_2026-10-10/candidate_summary.csv), and [run manifest](results/c5g7_layout_smoke_2026-10-10/run_manifest.json); full statepoints/logs are in the [workflow artifact](https://github.com/thenextw4ng/cb-pfr/actions/runs/38085586809). These are exploratory smoke tests, not benchmark-grade results or a robust candidate ranking. The six layouts are not all official benchmark reference cases. The canonical arrangement is a baseline identity check; physical ranking must wait for reviewed model/material correspondence, independent repeated runs per layout, and a predeclared reference/acceptance protocol. The current archived Stage 3–4 statepoints are not valid independent-seed repetitions; see [the provenance audit](reports/stage34_statepoint_provenance_audit_2026-10-11.md).

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
