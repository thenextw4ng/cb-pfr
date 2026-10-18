# Independent Reviewer Packet: CB-PFR A–G Physical Evidence — 2026-10-18

## Purpose and disposition

This packet is for a reviewer who is independent of the implementation and has relevant reactor-physics / Monte Carlo transport expertise. It is **not** a self-issued physical-validation certificate. No reviewer identity, approval, or sign-off is pre-filled.

**Current overall disposition: NOT PHYSICALLY VALIDATED.** The questions below must be answered from the exact archived input/output files. The code, run summaries, and public benchmark source alone do not establish that generated inputs were faithful or that the candidate-selection objective is physically accepted.

Review decision choices for every item: `PASS`, `FAIL`, `BLOCKED`, or `INCONCLUSIVE`. For any `PASS`, record the evidence path/hash and reasoning.

---

## Review A — C5G7 model identity and benchmark fidelity

### Frozen source and deliberate adaptation
- Primary repository: [mit-crpg/benchmarks](https://github.com/mit-crpg/benchmarks)
- Frozen upstream revision: `ba41bee54320ada0b4ac39a0dd2ca3c1d090a450`
- Model builder: [c5g7/openmc/2d/build-xml-2d.py](https://github.com/mit-crpg/benchmarks/blob/ba41bee54320ada0b4ac39a0dd2ca3c1d090a450/c5g7/openmc/2d/build-xml-2d.py)
- Material-group construction: [c5g7/openmc/materials.py](https://github.com/mit-crpg/benchmarks/blob/ba41bee54320ada0b4ac39a0dd2ca3c1d090a450/c5g7/openmc/materials.py)
- Tally definition: [c5g7/openmc/tally.py](https://github.com/mit-crpg/benchmarks/blob/ba41bee54320ada0b4ac39a0dd2ca3c1d090a450/c5g7/openmc/tally.py)
- Runner / group-structure patch: [scripts/run_c5g7_layout_study.py](https://github.com/thenextw4ng/cb-pfr/blob/experiment/c5g7-independent-physical-crosscheck-20261018/scripts/run_c5g7_layout_study.py)

### Required reviewer checks
1. Compare the **actual generated** `geometry.xml`, `materials.xml`, `settings.xml`, `tallies.xml`, `mgxs.h5`, source files, logs and statepoint from one representative run to the pinned benchmark definition.
2. Confirm material IDs/compositions, MOX enrichment regions, UO₂ composition, 17×17 pin locations, 21.42 cm assembly pitch, 3×3 arrangement, five fixed reflector locations and physical boundary conditions.
3. Confirm energy edges are exactly `[1e-5, 0.0635, 10, 100, 1000, 500000, 1000000, 20000000] eV`, and that the generated MGXS HDF5 metadata and group ordering match the transport data actually used.
4. Review all modifications to the upstream builder. The runner intentionally replaces the upstream log-spaced energy-group construction with standard C5G7 edges. Verify the actual run artifact, not only the patch source.
5. Confirm OpenMC version, cross-section provenance, settings, random seed, thread settings, tally definitions and output hashes are linked in the same run manifest.

**Provisional source-level observations (not reviewer approval):** the pinned upstream source has a nonstandard log-spaced `EnergyGroups` construction. CB-PFR patches the construction and audits the generated MGXS edge metadata. This demonstrates an identified discrepancy and a deliberate correction, but does not certify the entire generated model.

Reviewer decision: `[PASS / FAIL / BLOCKED / INCONCLUSIVE]`

Evidence / hashes:
- `[fill in]`

Physics-significant differences remaining:
- `[fill in; write “none” only if checked]`

Reviewer rationale:
- `[fill in]`

---

## Review B — Geometry, tally semantics and spatial mapping

### Frozen quantity definitions
- OpenMC mesh: `51×51×1`, three assemblies per axis and 17 pin bins per assembly.
- The two-by-two fuel-assembly block occupies 34×34 mesh bins: 1,156 bins.
- A 34×34 block contains 1,156 bins: 1,056 true fuel pins, 96 guide-tube cells with zero fission, and four central instrument/fission-chamber cells with tiny positive fission because the simplified chamber material contains trace fissile content. These four cells are not fuel pins and must be excluded from fuel-pin metrics.
- Reported objective: assembly-integrated fission-rate peaking proxy `max(R_a)/mean(R_a)`.
- This objective is a **relative fission-rate-shape proxy**, not absolute thermal power in watts, validated pin power, a safety limit, or a full-core power distribution.

### Required reviewer checks
1. Reconstruct the physical coordinate and HDF5 array ordering independently. Confirm the correct fuel-region block, axes, bounds and index orientation.
2. Inspect the new asymmetric synthetic HDF5 regression test in `tests/test_independent_c5g7_fuel_mask.py`; confirm it catches transpose, reflection or one-bin offset errors under the declared convention.
3. Confirm that the 1,056-true-fuel-pin mask excludes four central instrument tubes (local row/column 9,9 in each assembly) plus 96 guide-tube bins, and verify this against the actual generated assembly pin map.
4. Verify every reported (R_a) is reproducible from the same statepoint/tally, and that the aggregation and normalization are implemented as specified.
5. Verify cross-code metrics compare only matched positive fuel-pin bins and that non-fuel zero bins are excluded from relative-error calculations.

**Audit correction:** the initial mask was wrong because it treated four trace-positive central instrument/fission-chamber cells as fuel pins. The corrected postprocessing now uses 1,056 true fuel pins, excludes 100 non-fuel positions (four instrument tubes plus 96 zero-power guide tubes), and renormalizes each code's map over the same 1,056-pin set. The first JSON/CSV summary is superseded because the CSV had stale headers that left several fields blank; use the latest corrected posthoc summary artifact only.

Reviewer decision: `[PASS / FAIL / BLOCKED / INCONCLUSIVE]`

Coordinate/mapping evidence and hashes:
- `[fill in]`

Reviewer rationale:
- `[fill in]`

---

## Review C — QUBO/design-space and physical decision rule

1. Verify exactly 16 four-bit vectors are considered: six have exactly two MOX and two UO₂; ten violate cardinality.
2. Verify all six feasible layouts have equal cardinality-penalty QUBO energy. Therefore, this QUBO is a feasibility encoding and cannot discriminate neutronically superior layouts.
3. Confirm the five reflector positions stay fixed and each candidate ID is a deterministic map to its four material locations.
4. Review the physical objective and acceptance logic before approving any ranking: (k_\mathrm{eff}) acceptance, fission-rate-shape proxy, uncertainty and any hard constraints must be justified separately. Do not infer that larger or smaller (k_\mathrm{eff}) is intrinsically safer/better.
5. Determine whether three independent seeds per layout provide sufficient precision and statistical power for the proposed claim. Bootstrap resamples from those seeds are not additional independent transport runs.

Decision on mathematical mapping: `[PASS / FAIL / BLOCKED / INCONCLUSIVE]`

Decision on physical objective / acceptance rule: `[PASS / FAIL / BLOCKED / INCONCLUSIVE]`

Rationale:
- `[fill in]`

---

## Review D — Integrity, reproducibility and convergence

Required checks:
- Match each seed to input manifest, settings, MGXS hash, statepoint hash, raw HDF5 audit, logs and extracted tally data.
- Review within-run Monte Carlo standard deviation separately from between-seed sample variation.
- Review active-generation eigenvalue traces, source convergence / entropy diagnostics where applicable, and whether the sampling has reached a defensible stationary regime.
- Verify failures and `DIAGNOSTIC_REVIEW_REQUIRED` states are preserved as review requirements, not relabelled as convergence success.
- Confirm the P4/P5 campaign contains all six layouts × three seeds at both phases and that the P6 comparison consumes the actual held-out phase rather than the screening phase.

Campaign links:
- [P4/P5/P6 held-out OpenMC campaign #39098770358](https://github.com/thenextw4ng/cb-pfr/actions/runs/39098770358)
- [Independent Sₙ six-layout campaign #39104899024](https://github.com/thenextw4ng/cb-pfr/actions/runs/39104899024)
- [Corrected cross-code posthoc #39107216350](https://github.com/thenextw4ng/cb-pfr/actions/runs/39107216350)

Decision: `[PASS / FAIL / BLOCKED / INCONCLUSIVE]`

Missing / inconsistent records:
- `[fill in]`

Convergence rationale and evidence:
- `[fill in]`

---

## Review E — Trusted and experimental benchmark evidence

### Independent deterministic Sₙ comparator
Pinned solver: [EmreSakarya/c5g7-2d-transport-benchmark](https://github.com/EmreSakarya/c5g7-2d-transport-benchmark), commit `db421c969ee2de83e2d2ae2b14bda368567b558d`.

Its own [README and mesh-convergence report](https://github.com/EmreSakarya/c5g7-2d-transport-benchmark/blob/db421c969ee2de83e2d2ae2b14bda368567b558d/README.md) state that at 16 cells per pin it returns (k_\mathrm{eff}=1.184733), about −181.7 pcm versus 1.186550. The solver reports non-monotonic but improving mesh convergence from about −3616 pcm at four cells per pin to −182 pcm at sixteen cells per pin, attributing the residual to a Cartesian/digital-disk approximation of curved pin boundaries. This makes Sₙ a comparator with a known numerical-resolution bias, not a zero-bias acceptance oracle.

Required reviewer checks:
- Judge whether the declared mesh resolution is adequate for the comparison question; do not classify the known offset as an official benchmark tolerance or automatically as a CB-PFR model error.
- Check the corrected UMMU pin map on the matched 1,056-true-fuel-pin mask. The original solver console metric (normalized over 1,060 positive bins) reported a maximum near 2.3529, about 5.8% below the published MCNP maximum 2.498. After excluding four central instrument-tube cells and renormalizing over true fuel pins only, the posthoc maximum/minimum are 2.344035/0.217344 versus MCNP 2.498/0.232. The corrected metric still shows a discrepancy and is not a spatial-validation pass.
- Confirm a cross-code comparison remains distinct from experimental validation.

### BEAVRS experimental path
- Pinned upstream model: [mit-crpg/BEAVRS](https://github.com/mit-crpg/BEAVRS), commit `1ccae04dc3830a5977f08ed7f5f7e1e51ded0d22`.
- Observable: Cycle 1 day 0 tilt-corrected radial detector map at 58 instrumented labels.
- The recorded full-core runs and artifact-integrity checks completed, but the map agreement remains poor: normalized RMSE approximately 0.329–0.334; Pearson correlation approximately −0.078 to 0.032; mean absolute relative error approximately 27.7%–29.0%.
- The model compares those detector measurements to a normalized assembly-integrated U-235 fission-rate tally. That tally is a proxy, not an exact detector response operator. The recorded SE=230 control-bank override and axial step-width assumption also require review. The old coordinate-flip diagnostic must not be post-hoc fitted.
- Primary report: `reports/BEAVRS_CYCLE1_EXPERIMENTAL_COMPARISON_PROTOCOL.md`; coordinate audit: `reports/BEAVRS_COORDINATE_REGISTRATION_AUDIT_2026-10-11.md`.

Required reviewer decision for BEAVRS spatial observable: `[PASS / FAIL / BLOCKED / INCONCLUSIVE]`

Required reviewer decision for C5G7 computational comparison: `[PASS / FAIL / BLOCKED / INCONCLUSIVE]`

Evidence and rationale:
- `[fill in]`

---

## Review F — Evidence pipeline and release traceability

Automated evidence available:
- [Latest A–G foundation audit #39110583165](https://github.com/thenextw4ng/cb-pfr/actions/runs/39110583165)
- [Full-regression closeout #39110583360](https://github.com/thenextw4ng/cb-pfr/actions/runs/39110583360), with 211 tests passed
- [Corrected six-layout summary #39110583084](https://github.com/thenextw4ng/cb-pfr/actions/runs/39110583084), artifact #12130630849

The initial A–G foundation tests passed, including exact QUBO/layout checks and asymmetric HDF5 coordinate-order tests. A subsequent audit found the true-fuel mask and output CSV schema were wrong despite those tests passing. Regression tests have been expanded to cover instrument-tube exclusion, 1,056/4/96 population counts, fuel-only normalization, duplicate coordinates, and JSON/CSV consistency. This is a useful example of why CI pass status must not be treated as science acceptance.

Reviewer decision: `[PASS / FAIL / BLOCKED / INCONCLUSIVE]`

Evidence and rationale:
- `[fill in]`

---

## Review G — Scientific conclusion and permissible claim

The strongest claim may only be the narrowest one supported by the passed A–F gates. Unless the blockers above are closed, use:

> “CB-PFR is an uncertainty-aware screening and ranking workflow under evaluation on a specified six-layout C5G7 model using a declared relative fission-rate-shape proxy.”

Do not claim:
- universal physical superiority;
- reactor safety or a safe/best fuel design;
- experimental validation when spatial agreement and detector response are unresolved;
- general validation as a reactor-design method;
- that a successful workflow/CI run proves physics;
- quantum advantage without an appropriately controlled quantum-device comparison.

Final reviewer decision: `[PASS / FAIL / BLOCKED / INCONCLUSIVE]`

Reviewer name, qualifications and organization:
- `[reviewer completes]`

Date:
- `[reviewer completes]`

Signature / decision record:
- `[reviewer completes]`

## Overall final decision

Choose exactly one:
- `SOFTWARE_READY_ONLY`
- `SCIENTIFIC_READY_FOR_INDEPENDENT_REVIEW`
- `PHYSICALLY_VALIDATED_WITHIN_EXPLICIT_SCOPE`
- `NOT_READY / INCONCLUSIVE`

Current project disposition before independent review: **SCIENTIFIC EVIDENCE IN PROGRESS — NOT PHYSICALLY VALIDATED**.
