# C5G7 six-layout preparation audit — 2026-10-11

## Result

**Preparation passed; no transport calculation was run.** GitHub Actions staged the public MIT CRPG benchmark source, verified its pinned commit, regenerated the candidate enumeration, checked it against the frozen design-space manifest, and prepared six isolated model input cases.

- Workflow run: [C5G7 layout preparation audit](https://github.com/thenextw4ng/cb-pfr/actions/runs/38085033513)
- Prepared-case artifact: `c5g7-layout-study-prepared` on that workflow run.
- Upstream repository: `https://github.com/mit-crpg/benchmarks.git`
- Pinned source commit: `ba41bee54320ada0b4ac39a0dd2ca3c1d090a450`
- Frozen design-space manifest: `config/benchmarks/c5g7_2x2_design_space.json`
- Study summary status: `prepared_only`
- Candidate count: 6
- Each case contains a patched 2-D builder and recorded input hashes; the canonical reference arrangement is marked explicitly.

## Candidate layout space

Position order is `p00, p01, p10, p11`; U = UO2 and M = MOX.

| Candidate ID | Layout | Canonical reference arrangement? |
|---|---|---|
| `c5g7-2x2-UMMU` | U M / M U | Yes |
| `c5g7-2x2-MMUU` | M M / U U | No |
| `c5g7-2x2-MUMU` | M U / M U | No |
| `c5g7-2x2-MUUM` | M U / U M | No |
| `c5g7-2x2-UMUM` | U M / U M | No |
| `c5g7-2x2-UUMM` | U U / M M | No |

The five reflector positions `p02, p12, p20, p21, p22` are retained as fixed reflector positions by the adapter. The script refuses to patch if the expected upstream lattice assignment or runtime-setting lines differ from the audited template.

## Interpretation boundary

This is an explicitly reformulated **assembly-material placement** study. It is not a mapping from the legacy `fresh / once_burned / twice_burned` QUBO to C5G7. The canonical arrangement is a baseline identity check; the other five are design variants, not official benchmark reference cases.

The workflow did not run OpenMC transport and did not generate physical (k_\mathrm{eff}), flux, or power results for these six candidates. The prepared artifact must be reviewed and then executed only in an environment with the appropriate compatible OpenMC build and cross-section/MGXS data. Candidate ranking requires a predeclared objective, benchmark reference quantities, and acceptance protocol.
