# C5G7 P-1–P-3 discriminative-physics pilot (2026-10-18)

## Aim

Run a small but physically discriminative OpenMC budget ladder through the separately formulated C5G7 2×2 UO₂/MOX layout model. The pilot tests whether the low-budget screen exhibits observable layout differences and whether those observations persist for two deliberately contrasting layouts at larger transport budgets.

This is a **prospective exploratory study**. It does not establish official C5G7 benchmark acceptance, reactor safety, a validated physical ranking, or a treatment effect for CB-PFR.

## Design

The C5G7 model has exactly six layouts with two UO₂ and two MOX positions; five reflector positions remain invariant. The selected contrast pair is:
- **UMMU**: canonical/reference arrangement, used as the high-budget reference anchor.
- **MUMU**: selected from the prior three-seed smoke report because it had the lowest descriptive assembly fission-rate peaking proxy in that small sample. This is a hypothesis for comparison, **not** a declared physical winner.

P-1 screens all six feasible layouts. P-2 and P-3 repeat the same two-layout contrast. Total planned OpenMC transports: **10** (6 + 2 + 2).

| Phase | Layouts | Batches | Inactive | Particles/batch | Approx. active histories/run |
|---|---|---:|---:|---:|---:|
| P-1 low-budget screen | All six: MMUU, MUMU, MUUM, UMMU, UMUM, UUMM | 100 | 10 | 1,000 | 90,000 |
| P-2 intermediate | MUMU, UMMU | 2,000 | 100 | 5,000 | 9,500,000 |
| P-3 high-budget anchor | MUMU, UMMU | 20,000 | 500 | 10,000 | 195,000,000 |

The established project profiles are retained so results remain comparable with the repository's prior smoke, intermediate, and high-budget protocols. Because batch count, inactive count, and particles per batch all change across profiles, a cross-phase difference must be described as a **budget-profile sensitivity**, not as an isolated causal effect of history count alone.

## Seeds and provenance

Use upstream benchmark source commit `ba41bee54320ada0b4ac39a0dd2ca3c1d090a450`, OpenMC 0.16.0, standard C5G7 seven-group boundaries, unique output directories, raw HDF5 statepoint audits, source-convergence diagnostics, and the assembly-integrated fission-rate proxy. The same deterministic seed for a given layout is reused across budget profiles (UMMU: 610000; MUMU: 610002) to aid side-by-side budget sensitivity inspection. Reusing a seed does **not** create independent replicates and must not be treated as one.

Every completed run must preserve settings, seed, upstream revision, group-boundary audit, logs, statepoint, statepoint SHA-256, mesh tally evidence, raw HDF5 audit, source diagnostic, and fission-rate proxy. Source-convergence status `DIAGNOSTIC_REVIEW_REQUIRED` is an expected review flag, not an automatic pass.

## Interpretation gates

1. The workflow is evidence-integrity complete only if all 10 run records are present, all runs have parsed statepoints, raw HDF5 audits pass, the standard group-structure audit passes, and statepoint hashes are recorded.
2. Report (k_{\mathrm{eff}}\) with its within-run Monte Carlo standard deviation. Report assembly fission-rate peaking as a **relative-shape proxy**, not absolute power.
3. Inspect inactive/source-convergence diagnostics and compare uncertainty; do not infer convergence solely from job success.
4. Do not select a winner by maximum or minimum (k_{\mathrm{eff}}\). A defensible physical objective, design-specific acceptance limits, validated tally mapping/normalization, and independent review are still required.
5. Do not claim that CB-PFR outperforms point-estimate, QUBO-only, uniform-margin, or random selection from this pilot; those methods are not independently compared here.
6. Do not map the legacy `fresh / once_burned / twice_burned` QUBO categories to UO₂/MOX. This experiment uses a separate C5G7 assembly-placement formulation.

## Allowed result language

If all audits complete, the allowed statement is:

> A 10-run, three-budget-profile C5G7 OpenMC pilot screened six enumerated UO₂/MOX layouts at low budget and compared a prior-smoke contrast layout with the canonical arrangement at intermediate and high budgets. The results are exploratory screening evidence; convergence, official benchmark acceptance, a physically preferred layout, and CB-PFR selection effectiveness remain unestablished.

If a gate fails, report the campaign as incomplete and retain all available failure logs/artifacts. Do not silently drop failed runs.
