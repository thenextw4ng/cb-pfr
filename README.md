# CB-PFR — Confidence-Bounded Physical Feasibility Ranking

> An uncertainty-aware post-optimization selection layer for candidate configurations.

**Author:** Fahry Bagus Adiputra  
**Version:** 0.1.0  
**Status:** research prototype / methodological working paper

## Research question

Optimization can produce candidates that look good under nominal estimates but become fragile when downstream quantities are uncertain. CB-PFR studies whether candidate selection can become more conservative by incorporating uncertainty into the feasibility screen **after** optimization.

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
| CB-PFR implementation and automated CI | **Present; check the Actions badge/run for current status** |
| Abstract QUBO implementation and exact enumeration | **Present** |
| Reduced 1,000-trial synthetic benchmark runner and configuration | **Present** |
| Archived trial-level `results/per_seed_results.csv` | **Included; 4,000 method/trial rows (1,000 trials × 4 methods)** |
| Compiled methodological working paper PDF | **Included at `paper/CB-PFR_Methodological_Working_Paper.pdf`** |
| MC/DC C5G7 execution evidence | **Recorded execution evidence** |
| CB-PFR physical validation | **Not established** |
| QUBO → C5G7 mapping | **NO_DEFENSIBLE_MAPPING_FOUND** |
| Universal superiority | **Not claimed** |

## Recorded synthetic result

| Method | Selected true-feasibility rate |
|---|---:|
| QUBO-only | 0.857 |
| Point estimate | 0.933 |
| **CB-PFR** | **0.976 |
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
    ├── paper/
    │   ├── CB-PFR_Methodological_Working_Paper.pdf
    │   ├── README.md
    │   └── source/
    ├── src/cbpfr/
    │   ├── __init__.py
    │   ├── ranking.py
    │   ├── qubo.py
    │   ├── synthetic.py
    │   ├── experiments.py
    │   └── openmc.py
    ├── config/
    ├── results/
    │   ├── main_results.csv
    │   └── per_seed_results.csv
    ├── reports/
    ├── examples/
    ├── tests/
    ├── scripts/
    ├── docs/
    └── .github/workflows/tests.yml

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

This generates fresh trial-level output and aggregate/audit files from the checked-in code and configuration. The preserved archival `results/per_seed_results.csv` is provided for inspection and independent row-level comparison; a fresh run should not be described as an exact reproduction unless the environment, protocol, seeds, and row-level comparison have been checked. See [docs/reproducibility.md](docs/reproducibility.md), [docs/limitations.md](docs/limitations.md), and [FINAL_RELEASE_AUDIT.md](FINAL_RELEASE_AUDIT.md) for the evidence boundary.

## Design principles

- **Fail closed:** missing/invalid uncertainty does not silently pass.
- **Deterministic:** ranking and tie-breaking are explicit.
- **Auditable:** evidence provenance is separated from claims.
- **No invented physics:** abstract categories are not silently mapped to materials.
- **Reusable:** the method is separated from the manuscript.

## Research → inventor trajectory

    mathematical idea
          ↓
    formal specification
          ↓
    reference implementation
          ↓
    reproducible benchmark
          ↓
    package + examples + CI
          ↓
    independent users
          ↓
    external validation
          ↓
    new domains
          ↓
    measurable adoption

The repository currently documents the early stages honestly; later stages are future work.

## Citation

Use [CITATION.cff](CITATION.cff) for repository metadata and cite the working paper for methodological discussion.

## License

Code: MIT.  
Paper/documentation: CC BY 4.0.

## Author positioning

CB-PFR represents a research direction in **algorithmic decision-making under uncertainty**: separating optimization, uncertainty-aware feasibility screening, deterministic selection, evidence auditing, and physical-model validation boundaries.
