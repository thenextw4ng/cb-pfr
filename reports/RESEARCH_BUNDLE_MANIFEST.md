# Research bundle manifest — CB-PFR / ReactorQ / C5G7–OpenMC

**Current branch:** `main`  
**Evidence snapshot:** 2026-10-11  
**Purpose:** identify the committed project archives, machine-derived OpenMC evidence, reproducibility tools, and unresolved scientific gates.

## Committed archives

- `CBPFR_ReactorQ__Archive_2026-10-11.zip`: 86 historical artifacts recovered from prior conversations and the ChatGPT Library. Older versions are preserved for provenance and are not automatically current or validated.
- `OpenMC_HDF5_Evidence_2026-10-11.zip`: local production and stage34 OpenMC statepoints, summaries, XML/settings, logs, and run metadata.

Both ZIP archives are committed to `main`. Their integrity and member hashes are checked by `scripts/audit_evidence_archive.py`.

## Raw production statepoint audit

The production statepoint was read using the OpenMC 0.16.0 Python API in the OpenMC evidence workflow. A second CI check now reads the HDF5 bytes directly from the committed ZIP using h5py.

- ZIP member: `c5g7-run/2d/statepoint.20000.h5`
- SHA-256: `0d76dc1a14a2b74a388c01883f01e5c3095480d53eee885910ca2a0c57e6b882`
- Size: 1,158,736 bytes
- (k_{eff}) mean: 1.186394144702191
- Reported standard deviation: 5.6113408647969484e-05
- Settings: eigenvalue, multi-group, 20,000 batches, 500 inactive, 10,000 particles/batch, 19,500 active realizations
- Mesh: 51 × 51 × 1
- Scores: flux, fission, nu-fission
- Raw-HDF5 comparison: 10/10 checks passed on Python 3.10, 3.11, and 3.12

Workflow: https://github.com/thenextw4ng/cb-pfr/actions/runs/38096943383

This verifies the extracted statepoint values and agreement with the transcribed summary. It does not establish that the model reproduces the benchmark specification or validate any candidate layout.

## Main reproducibility and audit tools

- `scripts/audit_openmc_statepoint.py`: OpenMC API-based metadata/tally export.
- `scripts/audit_openmc_hdf5_archive.py`: raw HDF5 consistency audit from the committed ZIP.
- `scripts/compare_openmc_baseline.py`: fail-closed comparison of API-derived audit output against the recorded baseline summary.
- `scripts/inventory_openmc_runs.py`: artifact inventory and SHA-256 checksums.
- `scripts/audit_evidence_archive.py`: ZIP CRC verification and archive-member hashes.
- `reports/openmc_statepoint_audit_2026-10-11.md`: production scalar and tally audit.
- `reports/stage34_statepoint_provenance_audit_2026-10-11.md`: provenance/independence audit for recovered stage34 outputs.
- `reports/physical_simulator_validation.md`: benchmark comparison and physical-validation boundary.
- `reports/REMAINING_WORK_AUDIT_2026-10-11.md`: current completed-vs-blocked work status.

## Remaining scientific gates

1. Review geometry, boundary conditions, material definitions, MGXS provenance, and exact correspondence to the primary 2-D C5G7 benchmark specification.
2. Treat the three recovered stage34 statepoints as **not proven independent**: their colocated settings files are identical and lack explicit seeds; separately seeded settings have no matching statepoints in the archive.
3. Establish stable candidate IDs and exact configuration/input hashes for each physical run.
4. Decide whether to pursue a separate C5G7 two-UO2/two-MOX assembly-placement formulation or provide a source-backed depletion/material map for the legacy abstract QUBO. Do not silently map fresh/once-burned/twice-burned states to UO2/MOX categories.
5. Run and compare candidate layouts only after a reviewed model, predeclared common computational budget, and acceptance protocol are established.
6. Update the manuscript from verified candidate-level results; do not claim physical CB-PFR validation or reactor-safety evidence from scalar statepoint parsing alone.

## Interpretation rule

A ZIP integrity pass is a byte-integrity check. A raw-HDF5/OpenMC API pass is a data-extraction and consistency check. Software CI verifies software behavior. None of these alone proves benchmark correctness, candidate-level physical performance, independent repetition, or reactor safety.
