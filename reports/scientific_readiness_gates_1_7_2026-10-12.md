# CB-PFR scientific readiness audit — gates 1–7

**Repository branch at audit:** `feature/scientific-core-hardening`  
**Audit date:** 2026-10-12  
**Scope:** scientific core and reproducible C5G7/OpenMC workflow. UI/documentation polish is out of scope.

## Executive decision

The software is **not yet scientifically validated end-to-end**. Code-level integrity checks and a reproducible 18-run data set exist, but primary-specification sign-off, a justified source-convergence decision, benchmark-compatible spatial validation, and the canonical high-budget confirmation are still outstanding. Do not select a winning material layout or make a reactor-safety claim.

## Gate register

| Gate | Current evidence | Status | Remaining action |
|---|---|---|---|
| 1. Model identity and provenance | Pinned upstream repository/commit; standard C5G7 group boundaries in exported run evidence; MGXS hash recorded; separate input-provenance workflow exists. | PARTIAL — NOT SIGNED OFF | Review generated geometry, materials, settings, boundary conditions and MGXS against the primary benchmark specification; resolve production-versus-smoke XML differences; save an independent machine-readable sign-off. |
| 2. Reproducibility and integrity | 18 runs across six layouts and three unique seeds per layout; unique statepoint hashes; common MGXS hash; raw evidence export and HDF5 audit. | PASS FOR EXPORTED EVIDENCE | Re-run audit on canonical confirmation artifacts and preserve exact environment/commit provenance. |
| 3. Convergence and uncertainty | Existing entropy and k-generation diagnostic code; 18-run reported within-run keff SD was approximately 16.0–17.0 pcm, exceeding the provisional 10 pcm screen. | NOT PASSED / REVIEW REQUIRED | Execute the canonical confirmation profile; inspect complete traces and uncertainty; no automatic convergence certification based on a half-window difference. |
| 4. Physical tally and spatial mapping | Fission mesh extraction and structural mesh/lattice audit tooling exist; current fission-peaking values are normalized proxies. | STRUCTURAL TOOLING EXISTS; PHYSICAL VALIDATION BLOCKED | Independently verify bin order, lattice orientation, assembly integration, score definition, units and normalization; compare with a compatible primary benchmark spatial reference and uncertainty treatment. |
| 5. Objective and candidate decision | Six layouts enumerated under exactly two UO2/two MOX, reflectors fixed. No approved design-specific keff band/objective. | BLOCKED BY DESIGN | Keep all six layouts descriptive. Predeclare and justify objective/constraints before any future optimization claim; never use the canonical reference as a pass band for noncanonical layouts without justification. |
| 6. Software tests and fail-closed behavior | Scientific-core hardening and exhaustive QUBO tests are present; CI passed Python 3.10–3.12 on the audited branch head. | PASS AT AUDITED HEAD; FINAL INTEGRATION PENDING | Run full CI on the readiness PR; test malformed/missing evidence and verify candidate selection is blocked whenever required evidence or criteria are absent. |
| 7. Release and scientific reporting | Raw evidence and explicit non-claims exist. | NOT FROZEN | After gates 1–6 are resolved or explicitly marked limitations, tag a version and publish manifest, hashes, environment, commands, outputs, limitations and a reproducibility checklist. |

## Stage 4 — canonical confirmation run profile

Configuration: `config/benchmarks/c5g7_canonical_confirmation_profile.json`

- Model: pinned MIT CRPG C5G7 source commit `ba41bee54320ada0b4ac39a0dd2ca3c1d090a450`, OpenMC 0.16.0, standard seven-group boundaries.
- Candidate: canonical UMMU only. This is a numerical confirmation, not a six-layout optimization.
- Each run: 7,000 total batches, 500 inactive, 6,500 active, 10,000 particles per batch, one thread.
- Three independent seed bases: 720000, 730000, 740000.
- Budget: 70 million nominal histories per run; 65 million active histories per run; 210 million total nominal and 195 million active histories across three runs.
- The 10 pcm within-run SD target is provisional. The expected approximately 9.65 pcm estimate comes from idealized square-root scaling from the previous 22.5-million-active-history runs; it is not a guarantee.
- Preserve raw statepoints, batch-wise k-generation/entropy diagnostics, fission mesh proxy, hashes, run settings, aggregate JSON and Markdown.

### Required execution fix

The canonical workflow's aggregator requires `analysis/source_convergence.json`, but the existing workflow did not create that file before aggregation. This readiness change adds the missing diagnostic invocation for each statepoint. Without this step the aggregation stage would fail even if all three transport runs completed.

## What this audit does not certify

- No official C5G7 acceptance or independent primary-specification sign-off.
- No validated absolute power distribution; fission-rate peaking is a normalized proxy.
- No safety conclusion from (k_\mathrm{eff}) values.
- No winner among the six UO2/MOX layouts.
- No quantum advantage or hardware quantum-annealing claim.
