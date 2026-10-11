# OpenMC evidence handoff — 2026-10-11

This report links the existing CB-PFR repository evidence with a separately recorded local C5G7/OpenMC baseline. The repository's existing synthetic benchmark data and tests remain the authoritative evidence for the current CB-PFR software prototype.

## Existing repository evidence
The main branch already contains the CB-PFR implementation, tests/CI, the reduced synthetic benchmark runner and configuration, archival `results/per_seed_results.csv`, and methodological reproducibility/limitations audits. The recorded synthetic selected-feasibility rates are QUBO-only 0.857, point estimate 0.933, CB-PFR 0.976, and uniform margin 0.966. These are conditional synthetic results, not physical reactor results.

## Added local-run evidence
The `main` branch includes `OpenMC_HDF5_Evidence_2026-10-11.zip` at the repository root, alongside `evidence/openmc_local_baseline_2026-10-11/` metadata. GitHub Actions extracted the production statepoint and read it with the OpenMC 0.16.0 API; the derived `k_eff` mean and standard deviation matched the transcribed summary. See `reports/openmc_statepoint_audit_2026-10-11.md`. This verifies the scalar extraction, not benchmark validity or candidate-level physical validation. A second raw-HDF5 audit now independently reads the statepoint bytes from the ZIP and passed 10/10 checks across Python 3.10–3.12 ([CI run](https://github.com/thenextw4ng/cb-pfr/actions/runs/38096943383)); the statepoint SHA-256 is `0d76dc1a14a2b74a388c01883f01e5c3095480d53eee885910ca2a0c57e6b882`.

## Added reproducibility tools
- `scripts/audit_openmc_statepoint.py`: read-only extraction of scalar statepoint metadata and tally mean/std-dev values through OpenMC's API.
- `scripts/inventory_openmc_runs.py`: artifact inventory and SHA-256 checksums.

## Separate six-layout smoke-run evidence

The C5G7 layout workflow also completed six low-budget transport smoke runs with OpenMC 0.16.0. The common settings were 100 batches, 10 inactive, 1,000 particles per batch, one thread, and explicit seeds 620000–620005. All six runs completed and used the same MGXS SHA-256; the statepoint/input hashes and scalar results are preserved in `results/c5g7_layout_smoke_2026-10-10/`.

- [Full smoke-run workflow artifact](https://github.com/thenextw4ng/cb-pfr/actions/runs/38085586809)
- [Smoke-run scientific interpretation](c5g7_smoke_run_2026-10-10.md)

These runs verify that the isolated candidate cases can execute under the smoke profile. They do not provide benchmark-grade ranking or same-layout repeatability: there is one low-budget run per layout, and the canonical production and smoke materials XML differ. The six-layout study is a separate assembly-placement formulation, not a mapping of the legacy burnup-state QUBO.

## Still missing for a full candidate-level physical study
1. Stable candidate IDs and exact configuration vectors matched to each physical statepoint.
2. Verified proof that the five fixed reflector positions remain unchanged for each candidate.
3. A defensible QUBO-state-to-C5G7-material/depletion mapping, or a clearly separated and justified C5G7 assembly-placement formulation.
4. Independent candidate runs with documented seeds and per-run settings/log/statepoint hashes.
5. A predeclared benchmark comparison and physical acceptance protocol.

The production baseline statepoint has been read successfully through OpenMC 0.16.0, and its (k_\mathrm{eff}) mean/standard deviation match the transcribed summary. Three recovered stage34 statepoints also read successfully, but they have identical settings hashes with no explicit seed and nearly identical tallies; they must **not** be counted as independent repeated runs. The separate settings files with seeds 481730–481732 have no matching statepoints in the archive. See `reports/stage34_statepoint_provenance_audit_2026-10-11.md`.

Do not claim that six candidates have been physically simulated until candidate identity, input provenance, and independent statepoints are verified. The archive and software tools are now merged into `main`; physical CB-PFR validation remains unresolved.
