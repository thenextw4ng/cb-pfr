# CB-PFR C5G7 physical-validation decision — corrected review, 2026-10-12

## Executive decision

**Status: PHYSICAL VALIDATION NOT YET ESTABLISHED.** This decision supersedes the earlier wording that treated the four-fuel-position model as geometrically different from standard C5G7. The pinned upstream MIT-CRPG C5G7 implementation uses a 2-D quarter-core representation: a 2×2 fuel block with an L-shaped reflector in a 3×3 lattice. Therefore, the fact that the model contains four fuel assemblies does not by itself invalidate comparison with the standard 2-D benchmark. The repository's static model-identity review finds the dimensions, 17×17 pin lattices, assembly pitch, reflector placement, boundary-condition orientation, and corrected seven-group boundaries structurally consistent with the published 2-D C5G7 description. Independent primary-specification sign-off is still required before calling the model benchmark-faithful.

Primary references:
- OECD/NEA C5G7 benchmark description: https://www.oecd-nea.org/jcms/pl_13548/benchmark-on-deterministic-transport-calculations-without-spatial-homogenisation
- Song et al., *Frontiers in Energy Research* (2020), Table 1: https://www.frontiersin.org/journals/energy-research/articles/10.3389/fenrg.2020.00124/full
- Pinned model source: https://github.com/mit-crpg/benchmarks/tree/ba41bee54320ada0b4ac39a0dd2ca3c1d090a450/c5g7/openmc

## What is established

1. **Model structure — internal static review pass.** The archived generated model is structurally consistent with the 2-D quarter-core C5G7 representation. The 3×3 lattice contains four fuel assemblies and five fixed reflector positions; x/y bounds are ±32.13 cm; assembly pitch is 21.42 cm; each assembly uses a 17×17 pin lattice. The five reflector positions are invariant across the six design variants. This is an internal static review, not independent primary-specification sign-off.
2. **Energy-group structure — pass for the audited corrected runs.** The generated MGXS records the standard C5G7 seven-group boundaries [1e-5, 0.0635, 10, 100, 1000, 500000, 1000000, 20000000] eV. The historical nonstandard log-spaced-group runs must not be used as benchmark evidence.
3. **Run and artifact integrity — pass for the audited bundles.** The 18-run screen has six layouts × three seeds with unique statepoints and recorded hashes. The separate canonical UMMU confirmation has three unique seeds and statepoint hashes, raw HDF5 audits passing 22 checks per run, and recorded common geometry/MGXS provenance.
4. **Canonical scalar screen — provisional numerical pass.** The three-seed UMMU mean k-effective is 1.1864932118 versus published 1.18655, a difference of −5.6788 pcm. The between-seed sample SD is 15.5684 pcm and SEM is 8.9884 pcm. The combined-uncertainty z-score recorded by the project is about −0.434. These are numerical screening results; they do not replace model-identity review or source-convergence acceptance.
5. **Normalized spatial-shape screen — exploratory pass.** The maximum absolute relative difference between normalized integrated assembly fission-rate fractions and normalized published assembly-power fractions is 0.1790%; RMS relative difference is approximately 0.097%. All four differences are within the reference's stated relative uncertainty scale. A separate delta-method review gives |z| < 1 for all four bins under an independence approximation. This is a shape-only proxy comparison: it is not direct validation of absolute power, and the published reference covariance is unavailable.

## What remains open and why

| Gate | Current status | Evidence required to close |
|---|---|---|
| Primary model identity | BLOCKED pending independent sign-off | Qualified reviewer checks the exact primary specification against generated geometry, material compositions, boundary conditions, settings, and cross-section provenance; records discrepancies and signs the manifest. |
| Source/eigenvalue stationarity | DIAGNOSTIC REVIEW REQUIRED | Review complete batch-wise k-generation and entropy traces using a predeclared, justified criterion or qualified interpretation. No universal entropy-slope threshold is assumed. Extend inactive/active histories only if the traces or precision assessment require it. |
| Spatial observable comparability | EXPLORATORY ONLY | Independently approve mesh-to-assembly mapping, tally definition, normalization, and uncertainty propagation. The current tally is integrated fission rate, not absolute power in watts; reference covariance is unavailable. |
| Six-layout physical comparison | SCREENING ONLY | The higher-budget confirmation covers canonical UMMU only. All six layouts need comparable, common-budget transport evidence with sufficient convergence/precision before any physical ranking can be claimed. |
| Physical selection / optimization claim | BLOCKED | Predeclare a defensible physical objective and acceptance constraints. Do not choose a winner from k-effective alone or from the minimum QUBO energy. |
| Release software checks | CI pass on audited head; rerun required after this correction | Re-run the exact updated commit's tests and evidence audits; preserve workflow IDs, logs, and artifacts. |

### Batch-trace note

The archived 7,000-batch UMMU traces contain 6,500 active batches after 500 inactive batches. The active k-generation first-half versus last-half mean shifts are approximately +4.56 pcm (seed 720000), +3.81 pcm (seed 730000), and −2.15 pcm (seed 740000). Active entropy slopes and window differences are descriptive diagnostics, not an automatic pass/fail rule. These values do not alone prove non-convergence, but they also do not justify claiming stationarity without a declared acceptance rationale and review.

## Candidate-layout scope

The six layouts are a project-specific assembly-placement study with exactly two UO₂ and two MOX assemblies, not six official benchmark reference cases. The canonical UMMU arrangement is the one compared with the published reference. The other five layouts require a separate physical interpretation and should not inherit the canonical k-effective target automatically. The earlier 18-run campaign used 5,000 batches, 500 inactive, 5,000 particles/batch and is a screening campaign; it is not automatically a convergence-grade confirmation.

The assembly fission-rate peaking factor is defined as max(assembly-integrated fission rate) / mean(assembly-integrated fission rate). It is dimensionless and is not absolute power, a reactor-safety metric, or a validated design objective by itself.

## Release decision

- **Software reproducibility:** recent CI on the audited commit passed Python 3.10, 3.11, and 3.12 test jobs; the saved-statepoint recovery/analysis workflow also passed. The updated report commit must receive its own CI result.
- **Numerical benchmark screening:** provisional pass for canonical UMMU k-effective and exploratory normalized spatial shape.
- **Physical validation:** **NOT YET ESTABLISHED** pending independent primary-specification sign-off, source/eigenvalue stationarity review, spatial-tally comparability review, and adequate evidence for all six candidate layouts if a six-layout ranking is claimed.
- **Safety / absolute power / quantum advantage:** not claimed.

This decision is intentionally fail-closed. A green software test suite, a close central k-effective value, or a small normalized spatial residual cannot independently certify physical validation.
