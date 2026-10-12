# CB-PFR C5G7 model-identity review — 2026-10-12

**Review scope:** static comparison of archived generated OpenMC input files and the pinned upstream C5G7 model structure against published C5G7 descriptions. This is a reproducible internal technical review, not independent sign-off by an external reactor-physics reviewer.

## Primary source and scope boundary

- Pinned upstream implementation: [MIT-CRPG benchmarks, commit `ba41bee54320ada0b4ac39a0dd2ca3c1d090a450`](https://github.com/mit-crpg/benchmarks/tree/ba41bee54320ada0b4ac39a0dd2ca3c1d090a450/c5g7/openmc).
- OECD/NEA C5G7 is a seven-group transport benchmark; the MIT-CRPG repository describes 2D 2×2 UO2/MOX assembly arrays with reflector and a separate 3D extension: [repository overview](https://github.com/mit-crpg/benchmarks).
- Published reference values commonly reported for the 2D case are k-effective = 1.18655 with reference uncertainty around 9.5 pcm, and assembly powers 492.8 (inner UO2), 211.7 (each MOX), and 139.8 (outer UO2), with stated reference uncertainties. See [Frontiers, 2021](https://www.frontiersin.org/journals/energy-research/articles/10.3389/fenrg.2021.760339/full) and [Frontiers, 2020](https://www.frontiersin.org/journals/energy-research/articles/10.3389/fenrg.2020.00124/full).
- Only UMMU is the canonical diagonal UO2/MOX arrangement used for direct benchmark comparison. The other five UO2/MOX placements are project design variants; they must not be presented as six official benchmark cases.

## Static input comparison

The archived 18-run artifact from [Actions run 38182056526](https://github.com/thenextw4ng/cb-pfr/actions/runs/38182056526) contains generated geometry, materials, settings, tallies, MGXS, and statepoints for all six layouts.

| Check | Observed in generated input / provenance | Assessment |
|---|---|---|
| Core extent | x/y bounds at ±32.13 cm, i.e. 64.26 cm total | Matches published 2D C5G7 dimensions |
| Assembly pitch | 21.42 cm | Matches 17 pins × 1.26 cm pitch |
| Pin lattice | 17×17; pin cylinder radius 0.54 cm | Matches published geometry description |
| Assembly block and reflector | 3×3 lattice containing a 2×2 fuel block and L-shaped water reflector | Structurally consistent with the standard quarter-core model |
| Boundary conditions | x-min and y-max reflective; x-max and y-min vacuum | Equivalent to reflective left/top and vacuum right/bottom under the model coordinate convention |
| Energy groups | Explicit boundaries [1e-5, 0.0635, 10, 100, 1000, 500000, 1000000, 20000000] eV; audit records common group structure | Standard seven-group boundaries recorded as passing |
| Cross-section identity | One common MGXS hash reported across the 18-run evidence bundle; source is pinned to the upstream commit above | Provenance consistency passes; it does not independently prove every cross-section value against the primary report |
| Runtime and histories | The archived run was 5,000 batches, 500 inactive, 5,000 particles/batch, 2 threads | Executed transport evidence, but this was a screening/smoke budget, not convergence acceptance |

The generated model uses an explicit seven-group boundary array rather than the upstream builder's generic logarithmic group-boundary expression. This correction is necessary because C5G7 uses non-log-spaced group boundaries. The recorded MGXS group-structure audit passed on the archived 18-run evidence.

## Canonical numerical cross-check already available

A separate higher-budget canonical UMMU confirmation used three seed bases 720000, 730000, and 740000, each with 7,000 batches, 500 inactive, and 10,000 particles/batch. The audited aggregate mean k-effective was 1.1864932118, a difference of approximately −5.68 pcm from 1.18655; the combined-uncertainty z-score was approximately −0.434. This passes the project's provisional scalar numerical screen. It is not a formal benchmark acceptance certificate and does not validate all six layout variants.

## Critical spatial-tally limitation

The archived tally contains mesh/global `flux`, `fission`, and `nu-fission` scores. The assembly-level value used in the current selection workflow is a **fission-rate proxy**, not a direct power tally. The assembly-power reference is only comparable after the score definition, material-dependent fission energy treatment, spatial integration, normalization, and uncertainty/covariance assumptions are justified. A close normalized shape alone cannot close this gate.

The 2020 Frontiers report provides the reference assembly-power values and uncertainty scale (inner UO2 492.8 ± 0.10%, MOX 211.7 ± 0.18%, outer UO2 139.8 ± 0.20%) and demonstrates that assembly power and pin power are separate benchmark observables. These values should not be treated as a direct one-to-one reference for an unconverted fission-rate tally.

## Exploratory normalized spatial-shape comparison

The existing canonical UMMU spatial audit compared normalized assembly fission-rate fractions with normalized published assembly-power fractions. This is a **shape-only exploratory comparison**, not direct power validation.

| Assembly bin | Observed normalized fission-rate fraction | Reference normalized power fraction | Relative difference | Approx. combined z |
|---|---:|---:|---:|---:|
| p00 | 0.4669140 | 0.4666667 | +0.0530% | +0.584 |
| p01 | 0.2005424 | 0.2004735 | +0.0344% | +0.216 |
| p10 | 0.2003942 | 0.2004735 | −0.0395% | −0.240 |
| p11 | 0.1321494 | 0.1323864 | −0.1790% | −0.817 |

The z values use first-order uncertainty propagation, assume independent reference assembly-power estimates, and combine those with the between-run standard error from three normalized run-level fractions. A reference covariance matrix was unavailable. All four values lie within approximately one combined standard uncertainty under these assumptions, but this does **not** establish a benchmark pass: the computed quantity is a fission-rate proxy, not a demonstrated power-equivalent tally, and the covariance/tally-definition assumptions need review.

## Gate outcome

- **Static geometry / group-structure consistency:** internal review pass, with the source and coordinate convention documented above.
- **Canonical UMMU scalar k-effective numerical screen:** provisional project screen pass from the separate three-seed confirmation.
- **Independent model-identity sign-off:** still requires a reviewer to inspect the primary benchmark specification and sign the machine-readable manifest; this report is not a substitute for independent sign-off.
- **Source convergence:** the archived six-layout run remains review-required; a larger-budget six-layout transport campaign is being run separately. No convergence claim should be made until its raw batch traces are analyzed against declared criteria.
- **Assembly power / spatial acceptance:** blocked pending tally comparability and uncertainty treatment.
- **Six-layout physical winner:** not selected; no winner is justified by these checks.

**Bottom line:** the canonical input structure and standard group boundaries are consistent with the published 2D C5G7 description, and the canonical k-effective screen is numerically close to reference. The remaining physical-validation blockers are specific and testable: independent sign-off, source convergence, and a benchmark-compatible spatial power observable. This is benchmark verification, not reactor-safety certification.
