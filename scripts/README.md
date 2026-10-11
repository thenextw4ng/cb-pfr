# Research and audit scripts

These scripts are supported by the current repository and should be used according to their stated evidence boundaries.

## Core reproducibility

- `run_reduced_synthetic_calibration.py` — regenerate the frozen synthetic benchmark into a new output directory.
- `audit_recorded_results.py` — audit the released synthetic result table.
- `analyze_optimizer_experiment.py`, `validate_optimizer_runs.py`, and the `cbpfr.experiment_log` / `cbpfr.experiment_analysis` modules — validate optimizer-run records and summarize repeatability. Structural validity of a record does not prove its provenance.

## OpenMC evidence

- `audit_evidence_archive.py` — verify ZIP CRCs and compute SHA-256 hashes for archive members.
- `audit_openmc_statepoint.py` — use the OpenMC Python API to export statepoint metadata and tally means/standard deviations.
- `audit_openmc_hdf5_archive.py` — read the production HDF5 statepoint directly from the committed ZIP and compare its metadata, eigenvalue, mesh dimensions, and tally scores with the recorded baseline summary.
- `fingerprint_hdf5_semantics.py` — compare HDF5 byte hashes separately from canonical dataset-payload and full metadata fingerprints; useful when regenerated MGXS files have different byte serialization or tiny metadata differences.
- `compare_openmc_baseline.py` — fail-closed comparison between an API-derived audit JSON and the recorded summary.
- `inventory_openmc_runs.py` — inventory statepoints, logs, XMLs, manifests, and SHA-256 hashes.
- `run_stage34.py` and `run_stage34_fixed.py` — historical stage34 runners; recovered outputs must not be treated as independent runs unless seed/settings/statepoint provenance matches.

## C5G7 design-study tools

- `prepare_c5g7_reference.py` — clone and record the exact upstream C5G7 source revision.
- `enumerate_c5g7_layouts.py` — enumerate the six arrangements with exactly two UO2 and two MOX assemblies in the explicitly reformulated 2×2 design space.
- `run_c5g7_layout_study.py` — prepare isolated cases or optionally run them when the required OpenMC environment and data are available. Defaults are smoke-test settings, not benchmark-grade settings. The copied upstream `materials.py` is patched to pin the first and last C5G7 energy-group boundaries to exact `1e-5` and `1e7` before regenerating MGXS, preventing one-ULP drift across NumPy builds.
- `analyze_c5g7_repeatability.py` — aggregate three independent seed rounds across the six layouts; report between-run variability separately from within-run Monte Carlo SD and compute descriptive ranking stability.
- `audit_c5g7_validation_gates.py` — check repeated-run CSV integrity, common computational settings, seed/statepoint uniqueness, per-layout repeatability, and provisional scalar-reference screens; benchmark acceptance stays blocked without model-identity and spatial-tally review.
- `compare_c5g7_input_provenance.py` — compare archived production and regenerated canonical XML inputs, preserving exact hashes and attribute-normalized diffs for geometry, materials, settings, tallies, and plots.
- `analyze_c5g7_assembly_fission.py` — integrate the 51×51 mesh `fission` score into the four 17×17 fuel-assembly blocks and report a normalized fission-rate peaking proxy; it explicitly does not label this as absolute power and does not propagate correlated mesh-bin uncertainty.

## Important limits

- A passing unit test or CI run verifies software behavior, not reactor physics.
- A raw HDF5/API audit verifies data extraction and internal consistency, not that the model matches the official benchmark.
- The legacy abstract QUBO states `fresh / once_burned / twice_burned` are not mapped to C5G7 UO2/MOX or depletion states.
- The six-layout C5G7 formulation is a separate assembly-placement study; the canonical arrangement is a baseline identity check, not an optimization result.
- Do not claim candidate-level physical comparison until each statepoint is tied to a stable candidate ID, exact layout, settings, input hashes, and independent run provenance.
