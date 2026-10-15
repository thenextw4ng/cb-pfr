# Release Audit — Development Snapshot 0.3.0

**Audit date:** 15 October 2026  
**Repository:** `thenextw4ng/cb-pfr`  
**Status:** research-software development snapshot; not a formal tagged release; physical CB-PFR validation not established.

## Release identity

The package version declared in `pyproject.toml` is `0.3.0`. At audit time, the GitHub API reports no published release and no tag refs. No archival DOI has been assigned. The files `CITATION.cff` and `.zenodo.json` are aligned to a development snapshot; `.zenodo.json` is deposit metadata, not evidence of an existing Zenodo record. Until a release/tag and DOI are actually published, cite the immutable commit SHA.

## Code, paper, and dependency licenses

- Code license: `LICENSE-CODE.txt`, MIT.
- Paper/documentation license: `LICENSE-PAPER.txt`, CC BY 4.0.
- Python support declaration: `>=3.10` in `pyproject.toml`.
- CI version matrix: Python 3.10, 3.11, and 3.12.
- Dashboard requirements: `requirements-dashboard.txt` declares Streamlit, pandas, Plotly, h5py, and editable local package install.
- OpenMC 0.16.0, the C5G7 model input, and nuclear data are separately configured physical-simulation dependencies. They are not installed by the dashboard requirements.
- No fully resolved dependency lockfile, `environment.yml`, or container build is included. Exact dependency resolution is therefore not promised.
- Installation, test and reproduction instructions are documented in `docs/INSTALLATION_AND_REPRODUCIBILITY.md`.

## Actual visualization scope

- `app.py`: CB-PFR Simulator dashboard with a clearly labelled synthetic demo and an OpenMC preflight path. Opening the dashboard does not execute a fresh OpenMC transport run.
- `pages/01_C5G7_Layout_Explorer.py`: recorded candidate/layout table, layout schematic and comparative charts.
- `pages/02_Physics_Field_Explorer.py`: HDF5 extraction and visualization of actual archived 51 x 51 mesh-tally bins, with uncertainty displays and uploaded-statepoint inspection. The bin axes are not mapped to assembly materials; the maps do not represent absolute watts or a validated assembly-power distribution.
- `pages/06_High_Budget_Evidence.py`: separate 18-run record under `results/c5g7_high_budget_2026-10-12/run_level_evidence.json` using 5,000 batches and 5,000 particles per batch. It is distinct from the paper's primary 7,000-batch / 10,000-particle data archive.
- The visualizations are intended for research inspection and evidence provenance, not safety decisions.

## Experiment provenance and paper claims

### Primary six-layout archive

`CBPFR_ReactorQ__Archive_2026-10-11.zip` at the repository root contains the corrected-group six-layout campaign used for the paper's descriptive layout table: 6 layouts x 3 rounds = 18 records; rounds 820000/830000/840000; 7,000 total batches; 500 inactive; 10,000 particles per batch; two threads; unique statepoint hashes and common MGXS hash. The fission-peaking statistic is a relative assembly-integrated fission-rate proxy, not absolute power or a safety endpoint.

### Canonical scalar/reference screen

The separate UMMU confirmation uses seeds 720000, 730000 and 740000 at 7,000 batches / 500 inactive / 10,000 particles, with one thread per run. Mean (k_{\mathrm{eff}}) is 1.1864932; the difference from the saved reference 1.18655 is −5.679 pcm, with reported combined-uncertainty (z=-0.434). The normalized assembly-distribution comparison for that case has a maximum absolute relative difference of 0.179%. This is a numerical consistency check for one reviewed case, not a formal equivalence test or broad validation claim. The raw archive is supplied as a supplemental file in the Stage 8–10 delivery package but is not currently committed as a raw archive to GitHub. Summary audit JSON files are under `results/c5g7_canonical_high_budget_2026-10-12/`.

### Other evidence and explicit nonclaims

- The frozen synthetic benchmark contains 1,000 trials and rates of 0.857 (QUBO-only), 0.933 (point estimate), 0.976 (CB-PFR), and 0.966 (uniform margin). These are conditional on a synthetic generator, not reactor measurements.
- A separate synthetic confirmatory gain of +0.4875 percentage points did not meet its prespecified minimum of 2 percentage points.
- The retrospective equal-allocation ranking-and-selection baseline and CB-PFR selected the same layout (MUMU) on exploratory data; an incremental selection gain was not demonstrated.
- The path-integral annealing result is classical simulation, not QPU execution.
- The previous BEAVRS spatial-map comparison remains mismatched and is not validation evidence.
- Physical CB-PFR validation, a physically optimal layout, calibrated uncertainty coverage, a certified safety method, quantum advantage, and CB-PFR superiority are not established.

## CI and audit scope

The test workflow compiles Python sources, runs unit tests and examples, audits committed evidence and reproduces the frozen synthetic benchmark across the declared Python matrix. Passing CI supports the tested software behavior. It is not a reactor-physics validation certificate. The branding update initially exposed a stale dashboard test assertion; the test has been updated to expect the CB-PFR Simulator product name, and the follow-up workflow must finish before a green result is claimed.

## Remaining release steps

1. Wait for the CI workflow associated with the final closeout commit and record its final result.
2. Once the software snapshot is frozen, publish a reviewed Git tag/release (bump the version first if further source changes occur).
3. Archive that exact tag in Zenodo and add the DOI only after it is assigned.
4. Add a resolved dependency lock or container recipe only if strict environment reproduction is required.
5. Keep validation claims bounded until independent model-fidelity/source-convergence review and prospective physical acceptance criteria are available.
