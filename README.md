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
| CB-PFR implementation and automated CI | **Present; latest CI run passed** |
| Abstract QUBO implementation and exact enumeration | **Present** |
| Reduced 1,000-trial synthetic benchmark runner and configuration | **Present; reproducibility check is part of CI** |
| Archived trial-level `per_seed_results.csv` | **Not yet checked into this public repository** |
| Compiled methodological working paper PDF | **Not yet checked into this public repository** |
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

These are conditional synthetic benchmark results. They are not physical evidence and do not establish universal superiority.

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

This generates trial-level output and aggregate/audit files from the checked-in code and configuration. The original archival `per_seed_results.csv` is not currently included, so row-by-row comparison against that original artifact is not possible from this public repository alone. See [docs/reproducibility.md](docs/reproducibility.md) and [FINAL_RELEASE_AUDIT.md](FINAL_RELEASE_AUDIT.md) for the exact evidence boundary.

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

Use CITATION.cff for repository metadata and cite the working paper for methodological discussion.

## License

Code: MIT.  
Paper/documentation: CC BY 4.0.

## Author positioning

CB-PFR represents a research direction in **algorithmic decision-making under uncertainty**: separating optimization, uncertainty-aware feasibility screening, deterministic selection, evidence auditing, and physical-model validation boundaries.
