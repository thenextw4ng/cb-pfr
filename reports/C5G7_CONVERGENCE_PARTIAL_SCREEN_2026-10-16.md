# C5G7/OpenMC convergence diagnostic screen — partial snapshot

- **Study ID:** `CBPFR-C5G7-convergence-screen-2026-10-16`
- **Status:** `INCOMPLETE_OR_DUPLICATE_ARTIFACTS`
- **Scope of this report:** 14 available artifacts only (13 production records and one low-budget V2a record). This is not the full 75-production + 1,200-V2a campaign and is not a random/representative sample.
- **Convergence certified:** **No**
- **Official benchmark acceptance:** **No**

## Operational screens applied

The current triage screens require at least 100 active trace values; absolute first-half/second-half k-generation mean shift ≤25 pcm; absolute OLS k-generation slope ≤25 pcm per 1,000 active batches; absolute first-to-last-quartile relative entropy drift ≤0.1%; absolute relative entropy slope ≤0.1% per 1,000 active batches; a passing raw-HDF5 audit; and zero fission-source sites outside the entropy mesh.

These cutoffs were set after preliminary spot-checks and are **operational triage thresholds, not official C5G7 limits, a blinded confirmatory test, or a convergence certificate**. A pass means no listed alarm fired; it does not prove convergence.

## Snapshot result

| Group | Artifacts screened | Screen pass | Flagged for review |
|---|---:|---:|---:|
| Production P1–P4/V1a samples | 13 | 9 | 4 |
| Low-budget V2a sample | 1 | 0 | 1 |
| **Total** | **14** | **9** | **5** |

All 13 sampled production artifacts passed the raw-HDF5 audit and had zero entropy-mesh warnings. The flagged production samples were:

- P1–UMMU, seed 1268052158: k-generation half-shift −31.21 pcm.
- P1–UMMU, seed 48880955: k-generation half-shift −67.75 pcm.
- P2–MUUM, replicate 10: k-generation half-shift +60.80 pcm.
- P3–MMUU, replicate 7: k-generation half-shift −27.41 pcm.

The single sampled V2a–UMUM case (800 batches, 500 inactive, 2,000 particles/batch) failed four operational diagnostics: k half-shift −1,423.17 pcm; k-generation slope −6,622.18 pcm per 1,000 active batches; relative entropy quartile drift 0.1998%; relative entropy slope 0.9378% per 1,000 active batches. This low-budget observation should not be used as a high-budget physical reference.

## Interpretation and follow-up

This screen demonstrates why the source/eigenvalue trace should be reviewed per run rather than treating a successful transport process or raw-file audit as proof of convergence. It does **not** establish that all campaign runs fail or pass.

The full campaign analysis remains data-gated until all 75 production runs and 1,200 V2a observations are available and pass integrity checks. Then review all flagged traces, inspect source/mesh causes, and choose targeted additional inactive/active histories or model/mesh repairs. Do not blindly rerun every candidate. The final campaign workflow deliberately keeps `convergence_certified=false`.

## Provenance

- Operational thresholds: [`c5g7_convergence_screen_v1.json`](../config/benchmarks/c5g7_convergence_screen_v1.json)
- Analyzer: [`analyze_c5g7_convergence_study.py`](../scripts/analyze_c5g7_convergence_study.py)
- Campaign aggregation: [`c5g7-v2a-aggregate.yml`](../.github/workflows/c5g7-v2a-aggregate.yml)
- Campaign production: [GitHub Actions run 38769477847](https://github.com/thenextw4ng/cb-pfr/actions/runs/38769477847)
- V2a shards: [0](https://github.com/thenextw4ng/cb-pfr/actions/runs/38769481470), [1](https://github.com/thenextw4ng/cb-pfr/actions/runs/38769485693), [2](https://github.com/thenextw4ng/cb-pfr/actions/runs/38769489040), [3](https://github.com/thenextw4ng/cb-pfr/actions/runs/38769492881), [4](https://github.com/thenextw4ng/cb-pfr/actions/runs/38769496757).
