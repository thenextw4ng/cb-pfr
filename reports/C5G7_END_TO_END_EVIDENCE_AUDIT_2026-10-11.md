# C5G7 end-to-end run-evidence audit

**Status: implementation added; this document does not claim a new simulation has run.**

## Purpose

The runner, raw-HDF5 checker, and analysis scripts already cover different parts of the pipeline. This gate connects their evidence so a completed study is not treated as usable merely because the OpenMC process returned zero.

## Command sequence

Run in the same OpenMC 0.16.0 environment and against the actual study directory:

```bash
python scripts/run_c5g7_layout_study.py \
  --source-root /path/to/pinned/mit-crpg-benchmarks \
  --design-space config/benchmarks/c5g7_2x2_design_space.json \
  --output /path/to/new-study \
  --mode run --batches 100 --inactive 10 --particles 1000 --threads 1 \
  --seed-base 620000

python scripts/audit_c5g7_smoke_statepoints.py \
  --study-summary /path/to/new-study/STUDY_SUMMARY.json \
  --out /path/to/new-study/analysis/raw_hdf5_audit.json

python scripts/audit_c5g7_evidence.py \
  --study-summary /path/to/new-study/STUDY_SUMMARY.json \
  --design-space config/benchmarks/c5g7_2x2_design_space.json \
  --raw-audit /path/to/new-study/analysis/raw_hdf5_audit.json \
  --out /path/to/new-study/analysis/evidence_integrity_audit.json
```

The output directory must be new; the runner and audit do not overwrite existing outputs. The numbers above are smoke settings only. A PASS means the audit's software/provenance checks agree, not that the physics is benchmark-grade.

## Fail-closed checks

- Exactly six unique two-UO2/two-MOX layouts; stable IDs/signatures; one canonical reference arrangement.
- The design contract lists precisely `p02, p12, p20, p21, p22` as fixed reflector positions.
- For every candidate, the generated lattice assignment is checked against the expected 3×3 layout. The right-hand reflector column and bottom reflector row must remain `w`.
- `CASE_RESULT.json`, `STUDY_SUMMARY.json`, and the recorded output hash map must agree.
- Every file named in the post-run hash manifest must exist and match SHA-256; unsafe paths are rejected.
- Build and transport logs must exist and be nonempty; both recorded commands must have exit code zero.
- Settings XML must parse and match the common batches/inactive/particles profile and the candidate's explicit seed.
- Statepoints must be present, unique by hash, and included in the hash manifest; seeds must be distinct.
- All six candidates must use one shared nonempty MGXS hash.
- The raw-HDF5 audit must be PASS and match the same candidate IDs and statepoint hashes.

## Tally and statistical pipeline

The existing scripts remain the source of tally-derived quantities:

- `scripts/audit_openmc_statepoint.py` exports tally means and standard deviations from OpenMC's API.
- `scripts/analyze_c5g7_assembly_fission.py` aggregates the 51×51 fission mesh into four 17×17 assembly blocks and reports the normalized fission-rate peaking proxy.
- `scripts/analyze_c5g7_fission_objective_repeatability.py` reports the per-seed objective and between-seed variability.
- `scripts/analyze_c5g7_repeatability.py` checks run identity and reports repeated-run variability and descriptive rank stability.
- `scripts/build_c5g7_layout_selection_qubo.py` requires an explicit design-specific k-effective band and only acts on already-scored candidates.

Do not treat correlated mesh-bin standard deviations as independent or call the peaking proxy absolute power. Report within-run Monte Carlo uncertainty separately from between-seed variability. Do not declare a winning layout while the objective mapping, spatial alignment, acceptance band, or common-budget/convergence gate is unresolved.

## Evidence boundary

The fixed-reflector check is input-generation evidence, not proof that the entire reactor model is correct. Hash consistency proves artifact identity, not physical validity. The legacy `fresh / once_burned / twice_burned` QUBO remains unmapped to C5G7 UO2/MOX. No quantum advantage, benchmark acceptance, physical superiority, or reactor-safety claim follows from this audit.
