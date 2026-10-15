# CB-PFR / ICIMCIS 2026 — Release and Reproducibility Audit

**Audit date:** 15 October 2026  
**Repository:** `thenextw4ng/cb-pfr`  
**Branch:** `research/cbpfr-four-gate-closeout-2026-10-12`  
**Status:** development snapshot and review-paper build verified; formal release/DOI and physical validation remain unissued/unestablished.

## 1. Exact release state

The repository package version in `pyproject.toml` is `0.3.0`. The GitHub API returned an empty release collection and no tag refs at audit time. Consequently, `0.3.0` is a development package version, not a published tag/release. No Zenodo DOI is recorded. An exact commit SHA—not a guessed tag or DOI—is used in the accompanying closeout manifest.

Metadata discrepancies found in the previous state have been corrected on this branch:
- README now labels 0.3.0 as an untagged development snapshot and no longer promises an already planned 0.1.0 DOI.
- `CITATION.cff` now has version 0.3.0 and no release date.
- `.zenodo.json` is explicitly draft deposit metadata for version 0.3.0; its false implication of an existing 2026-10-05 release date has been removed.
- `pyproject.toml` already declared 0.3.0 and remains the package-version authority.
- App branding was aligned to “CB-PFR Simulator”; demo data remains explicitly labelled synthetic.

## 2. License, dependencies, and installation

- Code: `LICENSE-CODE.txt`, MIT.
- Manuscript/documentation text: `LICENSE-PAPER.txt`, CC BY 4.0.
- Python: `>=3.10` in `pyproject.toml`; CI matrix includes 3.10, 3.11, and 3.12.
- Dashboard requirements are declared in `requirements-dashboard.txt` (editable local package, Streamlit, pandas, Plotly, h5py).
- OpenMC 0.16.0 and nuclear-data/model setup are separate physical-simulation prerequisites; dashboard requirements do not install nuclear data or initiate transport calculations.
- There is no resolved dependency lockfile, environment.yml, or container recipe at audit time. The installation/reproducibility guide now states this explicitly rather than implying bit-for-bit environment locking.
- Installation and test commands are documented in `docs/INSTALLATION_AND_REPRODUCIBILITY.md`.

## 3. Actual dashboard visualization features reviewed

- `app.py`: synthetic demonstration and OpenMC preflight interface; it does not run OpenMC when opened. The visible title now matches the product name.
- `pages/01_C5G7_Layout_Explorer.py`: archived candidate table, layout schematic, and comparative plots.
- `pages/02_Physics_Field_Explorer.py`: reads the archived production HDF5 statepoint and plots the recorded 51 x 51 mesh tally fields and uncertainties. Axes are bin indices; the visualization does not infer assembly-material identity, absolute power, or a validated assembly map. It also supports inspection of an uploaded HDF5 statepoint, whose candidate provenance must be established independently.
- `pages/06_High_Budget_Evidence.py`: consumes `results/c5g7_high_budget_2026-10-12/run_level_evidence.json`, a separate 18-run archive at 5,000 batches and 5,000 particles per batch. This viewer data are not interchangeable with the manuscript's 7,000-batch/10,000-particle six-layout archive.

## 4. Experiment artifacts and claim alignment

### A. Primary six-layout archive used for descriptive layout means
`CBPFR_ReactorQ__Archive_2026-10-11.zip` is in the repository root. It holds the six-layout, three-round (18-run) corrected-group campaign, with rounds 820000/830000/840000, 7,000 batches, 500 inactive, 10,000 particles per batch, two threads, unique statepoints, and common MGXS provenance. The recorded fission-rate peaking statistic is a relative assembly-integrated proxy, not absolute power or a safety endpoint.

### B. Separate canonical UMMU scalar and spatial screen
The three-seed screen uses seeds 720000, 730000, 740000 at 7,000 batches/500 inactive/10,000 particles and one thread per run. The mean (k_{\mathrm{eff}}) is 1.1864932; the difference from the saved scalar reference 1.18655 is −5.679 pcm, with reported combined-uncertainty (z=-0.434). The single-case normalized assembly-distribution comparison reports a maximum absolute relative difference of 0.179%. This is a numerical consistency check, not formal equivalence, universal model validation, or proof of source convergence. The raw three-seed archive is included in the delivery package but is not presently committed to the repository; three summary audit JSON records reside under `results/c5g7_canonical_high_budget_2026-10-12/`.

### C. Synthetic benchmark
The repo contains a 1,000-trial synthetic benchmark and its trial-level results. Its selection rates (QUBO-only 0.857, point estimate 0.933, CB-PFR 0.976, uniform margin 0.966) are conditional on the synthetic generator. A separate confirmatory test's +0.4875 percentage-point gain did not meet its prespecified minimum of 2 percentage points.

### D. Ranking-selection comparison
The retrospective fixed-budget equal-allocation baseline and CB-PFR selected the same layout (MUMU) on the exploratory dataset; incremental selection gain was not demonstrated. The classical path-integral annealing test is not a QPU run. A prior BEAVRS spatial-map comparison remained mismatched and is not treated as physical validation.

## 5. Manuscript/PDF preflight

The anonymized ICIMCIS review manuscript is built from IEEEtran in A4 two-column format with three tables and no figures. The local submission package includes its matching LaTeX source and seven-entry BibTeX bibliography, plus the separate raw canonical UMMU archive needed to inspect that case. Preflight records include: number of pages, page dimensions, font embedding, citation/reference resolution, full-page rendered review, table readability, metadata anonymity, and a template-text scan. See the companion local audit for file hashes and build warnings.

The review manuscript deliberately omits the public repository URL and author identity. It is not an EDAS submission receipt. Upload and category checks must be performed in the live EDAS account.

## 6. Evidence limits

This audit verifies repository metadata, documented dependencies, installation instructions, software identity, available data archives, and the intended scope of the actual visualization code. It does **not** establish complete physical validation, an engineering-recommended layout, calibrated uncertainty coverage, or method superiority. It does not treat the successful CI or archive integrity checks as reactor-physics validation.

## 7. Remaining release actions

1. When ready to publish, create a reviewed, immutable Git tag/release for the exact 0.3.0 snapshot (or bump the version first if source changes continue).
2. Deposit that exact tag in Zenodo and only then add the assigned DOI to README/CITATION metadata and the camera-ready software citation.
3. Attach a resolved dependency lock or environment/container recipe if strict environment reproduction is required.
4. Keep all validation claims bounded until independent model-fidelity/source-convergence review and prospective physical criteria exist.


## Exact reproducibility identifiers (review build)

- **Software snapshot commit:** `442de59e40e440aad37da495b50a487992c8f096`
- **CI runs for that snapshot:** [38674523991](https://github.com/thenextw4ng/cb-pfr/actions/runs/38674523991) and [38674518908](https://github.com/thenextw4ng/cb-pfr/actions/runs/38674518908), both completed successfully on the 3.10/3.11/3.12 matrix.
- **Anonymized review PDF SHA-256:** `5038318b3af49b4cc1d1f1db75018edbf98647e5a035411624db4c82fa309960`
- **LaTeX source SHA-256:** `1b9c28bdc52f9d4b513a5e6bbb41dd059d8b23d27502f2da2db86ac8e4fc2d72`
- **BibTeX SHA-256:** `481cbb04c6110f857630ecbdbfa52797ba998845785bac50803b95295212cac8`
- **Primary six-layout evidence archive SHA-256:** `be48b17c2c336a97d08673d191457b9c695853759180116f5382f636b4c93019`
- **Supplemental canonical UMMU evidence archive SHA-256:** `b996708634ff41491b0323bdac11d5ab2574c6716d42fca1a8bf449795aca953`

The software snapshot commit predates this audit-note update, so its hash is a stable identifier for the reviewed code/metadata state. The additional audit-note commit records results about that immutable snapshot; neither is a tagged release, and no DOI is implied.
