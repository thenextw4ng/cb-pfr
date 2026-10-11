# Corrected-group C5G7 fission-peaking repeatability (smoke budget)

**Status: EXPLORATORY_DESCRIPTIVE_ONLY.** The corrected-group study completed 18 runs across three independent seed rounds and six 2×2 UO₂/MOX layouts. All 18 MGXS group-structure audits passed; all statepoint hashes are unique; all runs share the same corrected MGXS hash `a4328a7b012321fbe8f661745aa135f0a2eecd34cf475429e160865204acb129`.

| Layout | Mean k_eff | Between-seed SD(k_eff) | Mean fission peaking | Between-seed SD(F) | CV(F) | Descriptive F rank |
|---|---:|---:|---:|---:|---:|---:|
| MUMU | 1.14482492 | 0.00216958 | 1.296265 | 0.022605 | 1.744% | 1 |
| MUUM | 1.15847361 | 0.00209632 | 1.310279 | 0.022338 | 1.705% | 2 |
| MMUU | 1.14541306 | 0.00303635 | 1.327285 | 0.011865 | 0.894% | 3 |
| UUMM | 1.20511523 | 0.00201187 | 1.825391 | 0.024419 | 1.338% | 4 |
| UMUM | 1.20789406 | 0.00218814 | 1.855918 | 0.046896 | 2.527% | 5 |
| UMMU | 1.18610263 | 0.00386340 | 1.886113 | 0.028995 | 1.537% | 6 |

## Interpretation

The fission-rate peaking proxy is defined as max(assembly-integrated fission tally) divided by the mean of the four assembly-integrated fission tallies. It is dimensionless; it is **not absolute power or a reactor-safety metric**. The reported between-seed SD is the sample SD of this derived scalar across three independent runs; it is not a calibrated confidence interval.

A single-objective ranking would put MUMU first by the fission-peaking proxy, but its mean k_eff is about 1.1448, far from the standard C5G7 reference region. That demonstrates why minimizing peaking alone is not an acceptable design rule. No design-specific acceptable k_eff band has been approved, so **no layout is recommended or declared a winner**.

These runs used the corrected standard C5G7 energy-group boundaries `[1e-5, 0.0635, 10, 100, 1000, 500000, 1000000, 20000000]` eV and pinned upstream source commit `ba41bee54320ada0b4ac39a0dd2ca3c1d090a450`. However, they remain smoke-budget runs (100 batches, 10 inactive, 1,000 particles per batch), not benchmark-grade convergence. The legacy fresh/once_burned/twice_burned QUBO still has no defensible mapping to C5G7 UO₂/MOX compositions.

- Source smoke workflow: https://github.com/thenextw4ng/cb-pfr/actions/runs/38103007310
- Reanalysis workflow: https://github.com/thenextw4ng/cb-pfr/actions/runs/38103279843
- Machine-readable run-level data and summary are stored alongside this report.
