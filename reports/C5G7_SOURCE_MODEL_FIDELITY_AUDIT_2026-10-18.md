# C5G7 Source/Model-Fidelity Audit — 2026-10-18

## Disposition

**Gate A: PARTIALLY AUDITED; INDEPENDENT PHYSICS REVIEW STILL OPEN.** This report records checkable source-level facts and deliberate model adaptations. It does not certify the adapted CB-PFR model as physically validated.

## Pinned sources and input facts

- Primary upstream repository: [mit-crpg/benchmarks](https://github.com/mit-crpg/benchmarks)
- Pinned revision: `ba41bee54320ada0b4ac39a0dd2ca3c1d090a450`
- Primary model builder: [`c5g7/openmc/2d/build-xml-2d.py`](https://github.com/mit-crpg/benchmarks/blob/ba41bee54320ada0b4ac39a0dd2ca3c1d090a450/c5g7/openmc/2d/build-xml-2d.py)
- Material-group source: [`c5g7/openmc/materials.py`](https://github.com/mit-crpg/benchmarks/blob/ba41bee54320ada0b4ac39a0dd2ca3c1d090a450/c5g7/openmc/materials.py)
- Lattice geometry source: [`c5g7/openmc/lattices.py`](https://github.com/mit-crpg/benchmarks/blob/ba41bee54320ada0b4ac39a0dd2ca3c1d090a450/c5g7/openmc/lattices.py)
- Tally definition: [`c5g7/openmc/tally.py`](https://github.com/mit-crpg/benchmarks/blob/ba41bee54320ada0b4ac39a0dd2ca3c1d090a450/c5g7/openmc/tally.py)
- CB-PFR runner: [`scripts/run_c5g7_layout_study.py`](https://github.com/thenextw4ng/cb-pfr/blob/experiment/c5g7-physical-effectiveness-20261018/scripts/run_c5g7_layout_study.py)

### Finding A1 — The upstream energy-group construction requires an explicit correction

The pinned upstream `materials.py` constructs `EnergyGroups` with `np.logspace(-5, 7, 8)`. That sequence does not equal the standard C5G7 seven-group edges adopted by the project's protocol:

`[1e-5, 0.0635, 10, 100, 1000, 500000, 1000000, 20000000] eV`.

The CB-PFR runner contains a targeted replacement of this one audited source statement and audits the generated `mgxs.h5` group-structure attribute before transport. This is a deliberate source adaptation intended to avoid transporting with the nonstandard metadata. Each run must still retain the exact generated model files, post-patch hashes, and raw-statepoint audit; a passing group-structure audit alone does not prove all other model inputs are faithful.

### Finding A2 — The canonical lattice and boundary conditions are explicit

The upstream 2-D builder declares a 3×3 lattice with assembly pitch 21.42 cm and lower-left coordinate ((-32.13,-32.13)) cm. Its material layout is:

- Highest-y row: UO₂, MOX, reflector.
- Middle row: MOX, UO₂, reflector.
- Lowest-y row: reflector, reflector, reflector.

The upstream boundary definitions set west/north core boundaries reflective and east/south boundaries vacuum. OpenMC's documentation confirms that the first row supplied in `RectLattice.universes` corresponds to the highest physical (y)-value ([OpenMC geometry guide](https://docs.openmc.org/en/stable/usersguide/geometry.html)). The independent Sₙ source declares its core indices as west-to-east for (x), south-to-north for (y); this convention should remain part of the spatial-mapping regression contract.

CB-PFR's four fuel-position permutations alter only the four fuel positions in the explicit 3×3 C5G7 layout, with the five reflector positions fixed. This is a reformulated assembly-placement study, not the legacy burnup-state QUBO formulation.

### Finding A3 — The tally measures mesh-bin reaction rates, not absolute assembly power

The upstream 2-D mesh is 51×51×1 over the full 64.26 cm square domain and has scores `flux`, `fission`, and `nu-fission`. The mesh divides the 3×3 assemblies into 17×17 bins per assembly. For the two-by-two fuel region, the analysis extracts a 34×34 block. That block has 1,156 bins, but the independent Sₙ model identifies 1,060 fissionable fuel pins and 96 non-fuel/zero-power positions.

Accordingly, the cross-code shape comparison has been corrected to use the same 1,060-bin fuel mask for normalization and relative-error metrics. The 96 non-fuel bins are excluded; otherwise zeros in the reference field can make relative errors undefined and incorrectly report the minimum as zero fuel-pin power. The fuel-only mask correction is covered by regression tests in [A–G audit run #39106781314](https://github.com/thenextw4ng/cb-pfr/actions/runs/39106781314).

Even after this correction, OpenMC's mesh-integrated fission tally and the independent solver's normalized pin-power output are related but not identical physical quantities. This remains a code-to-code shape comparison, not a power validation or safety assessment.

## Evidence required to close Gate A

1. Preserve and hash each actual `geometry.xml`, `materials.xml`, `settings.xml`, `tallies.xml`, `mgxs.h5`, run log, statepoint and source-convergence diagnostic from the same run.
2. Compare those generated inputs against the pinned benchmark definition and the explicit adaptations above, not only against source filenames.
3. Reconfirm standard group boundaries and material-group ordering from the generated `mgxs.h5` and the raw statepoint's recorded energy mode.
4. Obtain a qualified independent reviewer to sign off the resolved discrepancies or mark each unreviewed item as a limitation.

## Evidence required to close Gate B

1. Verify mesh lower-left/upper-right bounds, orientation, Fortran/HDF5 storage order, fuel-block slice, and row/column coordinates with an independently reproduced index map.
2. Retain the 1,060-pin fuel mask, its source hash, and tests rejecting duplicate, missing, zero or non-finite matched fuel-bin values.
3. Report fission-rate shape as a relative proxy, separately from absolute power, heat deposition, safety limits, and normalized benchmark pin power.
4. Compare only like-for-like quantities and state the independent reviewer’s disposition.

## Current A–G decisions

| Item | Status | Reason |
|---|---|---|
| A — Source provenance and model identity | **PARTIALLY AUDITED / REVIEW OPEN** | Pinned code, lattice, boundaries and intentional energy-group correction identified; independent review of actual generated inputs remains required. |
| B — Tally semantics and spatial mapping | **CORRECTION IMPLEMENTED / REVIEW OPEN** | Fuel-only comparison now excludes 96 non-fuel bins; tally-to-physical-reference correspondence still needs independent review. |
| C — QUBO and design-space invariants | **SOFTWARE SUB-GATE PASSED** | Six layouts are enumerated exactly and the cardinality penalty is equal for all feasible variants; it does not rank physical layouts. |
| D — Integrity and convergence | **IN PROGRESS** | P4/P5 and six-layout Sₙ campaigns are not yet complete; stationarity is not certified by job completion. |
| E — Benchmark validation | **NOT ESTABLISHED** | Cross-code and experiment comparisons are still required; no physical acceptance band has been justified for alternative layouts. |
| F — Fail-closed pipeline | **SOFTWARE SUB-GATE PASSED** | Audit tests keep model, mapping, convergence and reference blockers explicit rather than auto-passing them. |
| G — Bounded claims and release | **BLOCKED ON A–E** | The current claim remains limited to evaluation of a screening/ranking method under the specified model and proxy. |

## Claim boundary

The most supportable claim remains that CB-PFR is an uncertainty-aware screening/ranking workflow being evaluated on a specified six-layout C5G7 assembly-placement study. Do not describe it as universally physically superior, experimentally validated, reactor-safe, or validated as a general reactor-design method until the applicable evidence gates have been independently closed.
