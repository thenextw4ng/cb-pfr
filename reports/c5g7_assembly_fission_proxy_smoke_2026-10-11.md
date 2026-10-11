# Assembly-integrated fission-rate proxy: six-layout smoke study

**Historical smoke evidence only:** these tallies were produced using nonstandard log-spaced energy-group boundaries inherited from the upstream builder. Do not use them for standard C5G7 benchmark acceptance or physical candidate ranking.

**Status: completed exploratory smoke analysis; not benchmark-grade and not a safety assessment.**

- Workflow: https://github.com/thenextw4ng/cb-pfr/actions/runs/38100954596
- Machine-readable results: [JSON](../results/c5g7_assembly_fission_proxy_smoke_2026-10-11.json) · [CSV](../results/c5g7_assembly_fission_proxy_smoke_2026-10-11.csv)
- Raw statepoints and per-candidate analysis: [workflow artifact](https://github.com/thenextw4ng/cb-pfr/actions/runs/38100954596/artifacts/11688080793)
- Model source: pinned `mit-crpg/benchmarks` commit `ba41bee54320ada0b4ac39a0dd2ca3c1d090a450`
- Budget: 100 batches, 10 inactive, 1,000 particles/batch, one seed per layout (seed base 650000).
- MGXS SHA-256: `170cc799f496e952465583bb078b2a88eae0f09886a821fd7ee8999d1eb93216`, byte-identical to the archived production library.

## Results

The mesh tally was divided into the four 17×17 blocks corresponding to the fuel assemblies in the 51×51 mesh. The score integrated was `fission`. The reported peaking factor is

\[
F_{\mathrm{fission}}=\frac{\max_a R_a}{\frac{1}{4}\sum_{a=1}^{4}R_a},
]

where \(R_a\) is the integrated fission-rate tally in assembly \(a\). Lower values mean a more uniform assembly-integrated fission-rate distribution for this particular metric; they do **not** establish a better or safer reactor configuration.

| Layout | \(k_\mathrm{eff}\) | Reported SD | \(F_\mathrm{fission}\) |
|---|---:|---:|---:|
| MMUU | 1.14929 | 0.00212 | 1.2800 |
| MUMU | 1.14026 | 0.00295 | 1.2807 |
| MUUM | 1.15677 | 0.00257 | 1.2992 |
| UUMM | 1.20277 | 0.00285 | 1.8003 |
| UMMU (canonical) | 1.18223 | 0.00259 | 1.8322 |
| UMUM | 1.20583 | 0.00226 | 1.8485 |

These values are descriptive smoke outputs only. The reported \(k_\mathrm{eff}\) uncertainty is large at this budget, and only one seed was used for each layout. The mesh-bin covariance is not propagated into uncertainty for \(F_\mathrm{fission}\), so this report does not assign confidence intervals to the peaking-factor differences.

## Interpretation and next gate

1. The six statepoints were successfully processed with the OpenMC 0.16.0 API, and the tally shape/score and assembly-block aggregation passed automated tests.
2. The MGXS file used by this run is byte-identical to the archived production MGXS file.
3. The peaking-factor ranking is **not** an optimization conclusion. It needs multiple independent seeds at a common higher budget, a reviewed mesh-to-assembly spatial alignment, and a justified physical objective/acceptance region.
4. The fission score is a normalized fission-rate proxy, not absolute power. A benchmark pin-power comparison requires the benchmark-compatible pin-level tally and normalization; this mesh aggregation cannot substitute for that reference distribution.

The script is `scripts/analyze_c5g7_assembly_fission.py`. Its geometry-index assumptions follow the pinned 3×3 model and OpenMC's documented top-down ordering for `RectLattice.universes` ([OpenMC geometry guide](https://docs.openmc.org/en/stable/usersguide/geometry.html)); the tally reshape uses OpenMC's `get_reshaped_data(expand_dims=True)` API ([OpenMC tally API](https://docs.openmc.org/en/stable/pythonapi/generated/openmc.Tally.html)). Independent spatial validation remains a release gate.
