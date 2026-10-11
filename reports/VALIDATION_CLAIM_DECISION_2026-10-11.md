# Validation claim decision — 2026-10-11

## Decision

**Do not yet label CB-PFR as experimentally or physically validated.** The strongest claims currently supported are: (1) CB-PFR is implemented as an uncertainty-aware post-optimization ranking method; (2) its 1,000-trial synthetic benchmark is reproducible under the declared protocol; (3) the software CI passes; and (4) the CB-PFR + one-hot QUBO selection pipeline has passed a smoke integration test using archived corrected-group C5G7 OpenMC results.

A pinned BEAVRS full-core OpenMC workflow has now run successfully once, but that first map comparison is **superseded** because the mesh covered 16 assembly pitches with 17 bins. Its low correlation is not valid evidence about the corrected model. The mesh extent has been fixed and raw tally statistical uncertainty is reported. Two assembly-aligned 17×17 mesh runs against the raw map completed but showed poor agreement (RMSE 0.34540 / correlation −0.05882 at 250 batches; RMSE 0.23688 / correlation 0.22991 at 500 batches). These are superseded because the benchmark provides a tilt-corrected map for simulation comparison and the run used the upstream SE=228 default rather than the recorded 230-step state. The final runner now uses a core-only 15×15 mesh (physically equivalent assembly-bin centers to the assembly-aligned 17×17 mesh, but without outer bins), the tilt-corrected map, shutdown bank SE=230, and the independent artifact-integrity audit. Only the first 17×17 attempt, which spanned 16 pitches, had incorrect mesh extent. The final corrected run is queued.

## What was checked

1. The BEAVRS workflow pins the public upstream model source at commit `1ccae04dc3830a5977f08ed7f5f7e1e51ded0d22`, installs OpenMC 0.15.3, downloads the official ENDF/B-VII.1 HDF5 data library, generates a full 3-D model, and compares a 58-position Cycle 1 day-0 normalized detector map with a mesh-integrated assembly fission-rate tally.
2. The first successful OpenMC transport used 250 batches, 30 inactive batches, and 2,000 particles per batch. It returned (k_\mathrm{eff}=0.998612\pm0.001239), normalized-map RMSE 0.37981, and Pearson correlation −0.21228. The tally mesh was mis-sized (17 bins across 16 assembly pitches), so the result is explicitly superseded and must not be used as validation evidence.
3. The corrected runner uses lateral mesh bounds of ±8.5 assembly pitches, reports raw per-bin tally standard deviations, and the workflow defaults to 500 batches, 50 inactive batches, and 3,000 particles per batch. The two raw-map runs are complete but superseded. The final corrected 15×15 / tilt-corrected run with SE=230 override and independent artifact audit is [here](https://github.com/thenextw4ng/cb-pfr/actions/runs/38117279412).
4. The separate C5G7 selection smoke workflow consumed 18 corrected-group OpenMC statepoints (six layouts × three seeds), checked unique statepoint hashes and common MGXS identity, and ran the CB-PFR + exact one-hot QUBO selector. Under explicitly illustrative limits, all six candidates passed the screen and MUMU was selected after enumerating all 64 binary selector states. This verifies pipeline consistency only; the limits are not benchmark-authoritative and the runs are exploratory smoke budget. [Workflow and artifact](https://github.com/thenextw4ng/cb-pfr/actions/runs/38116610735).
5. The synthetic 1,000-trial benchmark is evidence about the method under its declared synthetic data-generating process only. It is not nuclear experimental evidence.
6. No defensible mapping has been established from the legacy fresh / once_burned / twice_burned QUBO labels to physical fuel configurations. The explicit 2×2 C5G7 UO₂/MOX placement study is a separate reformulation, not a retroactive validation of the legacy QUBO.
7. QUBO formulation and exact classical enumeration do not prove quantum-device execution or quantum advantage.

## Claim matrix

| Proposed statement | Decision | Reason |
|---|---|---|
| “CB-PFR is an implemented uncertainty-aware post-optimization ranking method.” | Supported | Code and tests are in the repository. |
| “The released 1,000-trial synthetic benchmark reports a selected latent-feasibility rate of 0.976 for CB-PFR under its specified protocol.” | Supported with scope caveat | Reproducible synthetic evidence; not a universal superiority claim. |
| “The software test suite passes on Python 3.10, 3.11, and 3.12.” | Supported for recorded CI runs | This is software CI, not physical validation. |
| “CB-PFR and one-hot QUBO ran on an archived C5G7 OpenMC smoke dataset.” | Supported with scope caveat | Integration smoke passed under illustrative limits; not a benchmark-grade or safety result. |
| “A BEAVRS full-core OpenMC workflow has been executed.” | Supported with scope caveat | Full-core transport ran successfully; first run had a mesh defect, subsequent raw-map comparisons were poor and are superseded, and the final 15×15 mesh / tilt-corrected reference comparison is queued. |
| “The model is experimentally validated against BEAVRS.” | **Not yet supported** | Corrected comparison, uncertainty treatment, model-mismatch review, acceptance criteria, and artifact audit are not yet complete. |
| “CB-PFR physically improves nuclear-fuel loading optimization.” | **Not supported** | A defensible candidate-to-physics mapping, justified objective/constraints, benchmark-grade evaluations, and baseline comparison are not established. |
| “Quantum hardware was used / quantum advantage was demonstrated.” | **Not supported** | No real device/annealer run or fair quantum-vs-classical comparison is archived. |

## Exact wording recommended for paper, profile, and presentation

> I developed CB-PFR, an uncertainty-aware post-optimization candidate-ranking method for QUBO-generated candidate pools. Its implementation is accompanied by automated tests and a reproducible 1,000-trial synthetic benchmark. A separate C5G7 UO₂/MOX layout-selection prototype has passed a software integration smoke test on archived OpenMC runs. A pinned BEAVRS full-core model is being compared with public experimental detector-map data; corrected experimental comparison and physical effectiveness of CB-PFR remain under audit.

Short version:

> **Method/software and synthetic benchmark reproducible; nuclear experimental validation and physical ranking effectiveness not yet established.**

Do not shorten this to “physically validated” or “proven to improve reactor loading” until the corrected BEAVRS comparison and the separate candidate-effectiveness test pass their scientific gates.

## What would actually close the physical-validation gate

1. A successful corrected BEAVRS run with raw statepoint, input XML hashes, nuclear-data provenance, 58-position comparison CSV, tally statistical uncertainties, and independent artifact-integrity audit.
2. Resolve or quantify the known model-to-measurement mismatch: the day-0 summary reports bank E at 230 steps withdrawn while the upstream builder supports 228, and the model temperature differs by about 0.625 K from the reported inlet temperature.
3. Match the detector measurement operator more closely or explicitly justify the fission-rate proxy; account for measurement uncertainty and normalization-induced covariance.
4. Predeclare a benchmark-justified acceptance rule and independently review the input-to-result chain. A favorable correlation alone is not sufficient.
5. Separately, define a defensible physical candidate pool and compare CB-PFR against QUBO-only and other baselines using common compute budgets, repeated physical evaluations, and uncertainty propagation.
6. If claiming quantum execution or advantage, archive actual device/annealer runs and fair classical baselines. Otherwise describe the work as QUBO-based or quantum-compatible, not as demonstrated quantum advantage.

A successful BEAVRS model comparison would validate only the matched model/observable path. It would not automatically validate the legacy QUBO mapping or prove CB-PFR improves reactor optimization.

## Sources

- BEAVRS benchmark and public model: https://github.com/mit-crpg/BEAVRS
- BEAVRS Cycle 1 experimental comparison protocol: [reports/BEAVRS_CYCLE1_EXPERIMENTAL_COMPARISON_PROTOCOL.md](BEAVRS_CYCLE1_EXPERIMENTAL_COMPARISON_PROTOCOL.md)
- Corrected BEAVRS workflow: https://github.com/thenextw4ng/cb-pfr/actions/workflows/beavrs-cycle1-map-validation.yml
- C5G7 CB-PFR/QUBO smoke report: [reports/c5g7_cbpfr_selection_smoke_2026-10-11.md](c5g7_cbpfr_selection_smoke_2026-10-11.md)
- C5G7 selection workflow: https://github.com/thenextw4ng/cb-pfr/actions/workflows/c5g7-cbpfr-selection-smoke.yml
