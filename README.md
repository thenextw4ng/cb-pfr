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

## ReactorQ Studio dashboard (MVP)

On the `integration/reactorq-studio` branch, an optional Streamlit interface is available:

    pip install -r requirements-dashboard.txt
    streamlit run app.py

It demonstrates abstract QUBO candidate ranking and CSV/JSON export using explicitly labelled synthetic estimates. Its OpenMC panel performs **preflight checks only**; it does not launch a transport calculation. No physical keff, neutron-flux, or power result is produced by the dashboard. See [docs/reactorq_studio.md](docs/reactorq_studio.md) for setup and scientific limitations.


The branch also includes a repeatability analysis utility for recorded optimizer runs (`scripts/analyze_repeatability.py`) and a gated [OpenMC handoff checklist](reports/openmc_handoff_checklist.md). The repeatability utility analyzes supplied rankings; it does not run an optimizer or establish physical validity.

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
