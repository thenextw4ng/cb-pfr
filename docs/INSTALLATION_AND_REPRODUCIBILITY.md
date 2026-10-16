# CB-PFR Simulator: Installation and Reproducibility Notes

**Package snapshot:** `0.3.0` in `pyproject.toml`. This is a development snapshot, not a tagged release. As of 15 October 2026, no GitHub release tag or archival software DOI has been published. Cite an immutable commit SHA until a formal release is available.

## Scope and evidence boundary

CB-PFR is research software for post-optimization feasibility screening and ranking. The repository includes the ranking implementation, QUBO examples, tests, synthetic benchmark runner/results, C5G7/OpenMC layout tooling, statepoint/tally inspection, and audit reports. It is not a reactor-safety, licensing, or physically validated fuel-selection tool.

The code license is MIT (`LICENSE-CODE.txt`). The manuscript and documentation text are designated CC BY 4.0 (`LICENSE-PAPER.txt`). The project requires Python `>=3.10`; CI covers Python 3.10, 3.11, and 3.12. Dashboard dependency ranges are not a fully resolved lockfile: the repository does not currently supply an `environment.yml`, `requirements.lock`, or container image.

## Install and test the package

Use Python 3.10, 3.11, or 3.12.

```bash
python -m venv .venv
# macOS/Linux
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
python -m unittest discover -s tests -v
```

Install and run the optional Streamlit dashboard:

```bash
python -m pip install -r requirements-dashboard.txt
streamlit run app.py
```

The dashboard's built-in demo is synthetic and is explicitly labelled as such. The OpenMC mesh page reads archived statepoint data or an uploaded `.h5` file; opening the dashboard does not run a fresh neutron-transport simulation. Candidate schematics and comparison charts use recorded tables. The 51 x 51 mesh heatmaps show recorded tally-bin values, not a verified assembly/material map or absolute power distribution.

## OpenMC and nuclear data

The manuscript analyses use OpenMC 0.16.0 for the corrected-group transport campaigns. Reproducing transport runs requires a separately configured OpenMC installation, compatible nuclear data, and the specified model inputs. The audited seven-group boundaries are:

`[1e-5, 0.0635, 10, 100, 1000, 500000, 1000000, 20000000] eV`.

The model source is the MIT Computational Reactor Physics Group C5G7 benchmark repository pinned at upstream commit `ba41bee54320ada0b4ac39a0dd2ca3c1d090a450`. This is **model-input provenance**, not the CB-PFR software commit. Before running OpenMC, check source identity, geometry/material definitions, cross-section path, group boundaries, tally definitions, settings, and file hashes. A successful run or a close scalar `k_eff` is not, by itself, proof of physical validation.

## Separate experiment archives

Do not merge or conflate the following datasets:

1. **Primary six-layout archive in the manuscript:** `CBPFR_ReactorQ__Archive_2026-10-11.zip` at the repository root. Its corrected-group records cover six feasible layouts across three seed rounds (18 runs), rounds 820000/830000/840000, 7,000 batches, 500 inactive batches, 10,000 particles per batch, two threads, unique statepoint hashes, and a common MGXS hash. Its fission-peaking metric is a relative assembly-integrated fission-rate proxy, not absolute power.
2. **Canonical UMMU scalar/reference screen:** a separate three-seed archive (seeds 720000/730000/740000) with 7,000 batches, 500 inactive batches, 10,000 particles per batch, and one thread per run. The raw companion archive is included in the ICIMCIS Stage 8–10 delivery package, but is not currently stored as a raw archive in the GitHub repository. Summary audits are in `results/c5g7_canonical_high_budget_2026-10-12/`.
3. **Dashboard mesh demonstration:** `OpenMC_HDF5_Evidence_2026-10-11.zip` and `evidence/openmc_local_baseline_2026-10-11/`. This is a previously recorded production statepoint used to check HDF5 extraction/visualization; it is not the canonical three-seed screen archive.
4. **Separate high-budget evidence viewer:** `results/c5g7_high_budget_2026-10-12/run_level_evidence.json` records 18 runs at 5,000 batches and 5,000 particles per batch. It is distinct from the 7,000-batch/10,000-particle manuscript campaign.
5. **Synthetic benchmark:** `scripts/run_reduced_synthetic_calibration.py`, the frozen configuration, `results/main_results.csv`, and `results/per_seed_results.csv`. The selected-feasibility rates 0.857 (QUBO-only), 0.933 (point estimate), 0.976 (CB-PFR), and 0.966 (uniform margin) are conditional on the synthetic data-generating process. They are not reactor-performance measurements.
6. **Ranking-selection comparison:** `reports/C5G7_FIXED_BUDGET_RS_SQA_COMPARISON_2026-10-11.md`. CB-PFR and the retrospective equal-allocation baseline selected the same layout on the archived exploratory dataset; incremental selection gain was not demonstrated. Its path-integral annealing experiment was classical simulation, not QPU execution.

## Reproduction commands

To reproduce the reduced synthetic benchmark in a new, empty output directory:

```bash
python scripts/run_reduced_synthetic_calibration.py --results-dir results/reproduced_run
```

Run the test suite and examples:

```bash
python -m unittest discover -s tests -v
python examples/toy_qubo_example.py
python examples/basic_ranking.py
```

For C5G7 tools, follow `docs/C5G7_INTEGRATED_PIPELINE.md`, `docs/C5G7_HIGH_BUDGET_COMPUTE_PROTOCOL_2026-10-12.md`, and `config/benchmarks/c5g7_validation_protocol.json`. Supply physical limits only where a documented scientific rationale exists; illustrative command-line limits are not reactor-safety limits.

The `.github/workflows/tests.yml` workflow declares Python 3.10/3.11/3.12 and runs compilation, unit tests, examples, evidence audits, and the frozen synthetic benchmark. A passing CI run supports tested software paths; it does not independently certify neutron-transport model fidelity.

## Citation and release identity

Package metadata currently states version `0.3.0`, but there is no published GitHub release tag or Zenodo DOI. The software snapshot must be identified by the immutable Git commit SHA reported in the Stage 8–10 closeout. After a tagged release and archival DOI actually exist, update `CITATION.cff`, `.zenodo.json`, and the README to the exact release. Do not infer a DOI from the presence of `.zenodo.json`.
