# CB-PFR raw-statepoint audit and four-gate technical update

**Date:** 2026-10-12  
**Status:** deeper evidence audit completed; physical certification and superiority claim remain blocked.

## 1. Direct raw evidence
Downloaded and extracted the original GitHub Actions artifact `cbpfr-c5g7-six-layout-high-budget-confirmation-2026-10-12` (ID `11747677926`, 20,977,710 bytes). It contains 18 statepoints, 18 OpenMC logs, generated model XML/Python, per-run case JSON, and the run-level CSV.

## 2. Tally reconstruction — PASS for extraction consistency
For each statepoint, the audit read the mesh tally's `fission` score, reshaped the 51×51 mesh in OpenMC x-fastest order, summed the four 17×17 fuel-assembly blocks, excluded five reflector blocks, and recomputed `max(fuel-assembly integrated fission tally) / mean(four fuel-assembly integrated fission tallies)`.

The reconstructed proxy matches all 18 CSV values to floating-point precision; maximum absolute discrepancy is `2.22e-16`. Statepoints match CSV rows by seed. All 18 have mesh dimensions 51×51×1, 7000 batches, and 500 inactive batches. This verifies the extraction/arithmetic for the **relative fission-rate proxy**; it does not prove the tally is absolute power or that the physical model is benchmark-correct.

Mesh arithmetic is consistent: 64.26 cm / 51 = 1.26 cm per bin; 17 bins span 21.42 cm per assembly. The full mesh covers the 3×3 lattice, including four fuel assemblies and five reflector regions. The extraction explicitly selects the four fuel blocks adjacent to the symmetry corner.

## 3. Source convergence — preliminary diagnostic, not certification
Raw statepoints contain 7000-value Shannon entropy and per-generation `k_generation` histories. Entropy was absent from the summary CSV but **is present in the raw statepoints**; this corrects the earlier evidence limitation.

Descriptive entropy window means were computed for batches 501–1500, 2501–3500, and 6001–7000 across all 18 runs:
- Mean absolute first-to-last-window entropy-mean shift: `0.001061`.
- Maximum absolute shift: `0.003006`.
- Entropy fluctuations within windows are typically around 0.01–0.017.

There is no large uniform drift across all runs in these coarse summaries, but several runs have nonzero shifts and no threshold was preregistered. This is a diagnostic, not proof of convergence. Full traces and a documented trend procedure still need review; a longer-inactive/source-start sensitivity run is recommended. OpenMC explains that eigenvalue convergence can precede fission-source convergence and recommends source-distribution diagnostics such as Shannon entropy: https://docs.openmc.org/en/stable/usersguide/settings.html and https://docs.openmc.org/en/stable/methods/eigenvalue.html.

## 4. Canonical benchmark screen
The manifest identifies `UMMU` as the canonical arrangement (`p00=UO2, p01=MOX, p10=MOX, p11=UO2`). Its three-run mean `k_eff` is approximately `1.1864986`, around `−5.14 pcm` from the saved canonical reference `1.186550`. This is encouraging scalar agreement for the canonical case, not full validation of every permutation. Reference uncertainty/covariance and like-for-like spatial observables still need documentation.

Primary source: OECD/NEA, *Benchmark on Deterministic Transport Calculations Without Spatial Homogenisation: A 2-D/3-D MOX Fuel Assembly Benchmark*, NEA/NSC/DOC(2003)16: https://www.oecd-nea.org/upload/docs/application/pdf/2019-12/nsc-doc2003-16.pdf. The reference applies to the specified canonical case, not as a universal acceptance threshold for all permutations.

## 5. Physical acceptance rule
Keep the fail-closed rule: no physical acceptance without independent model/tally review and metric-specific criteria justified before ranking. Separate Monte Carlo uncertainty, between-seed variability, and reference uncertainty. Do not call the relative fission-rate proxy absolute power or a safety limit. Missing/incomparable criteria => `NO_SELECTION / INCONCLUSIVE`. No numeric thresholds were invented or fitted to observed results.

## 6. Fair comparison — exploratory only
The pre-physics composition QUBO `A*(sum(y_i)-2)^2` ties all six exactly-two-MOX layouts; it enforces composition but cannot rank physical performance. The post-physics selector QUBO is a separate formulation.

Leave-one-seed-round-out analysis selects `MMUU` in all three folds with zero observed held-out proxy regret. Uniform-random selection has expected held-out proxy regret around 0.272 per round on this proxy scale. This is descriptive only: three seed rounds, six layouts, no approved physical acceptance rule, and no independent confirmation set. It motivates a prospective test, not a confirmatory superiority claim.

For confirmation, freeze candidate set, model/MGXS hashes, acceptance rule, CB-PFR weights, tie policy, and endpoints on training seeds; compare CB-PFR with a specified random/tie baseline and any genuine pre-physics optimizer using identical physical-evaluation budgets and new held-out seed rounds. Count failures and compute cost.

## 7. Reproducibility freeze
The evidence package includes the original raw artifact, run-level CSV, audit script, JSON output, and this report. SHA-256 hashes are included in `SHA256SUMS.txt`. The raw artifact was not expired when downloaded, but Actions retention is not a durable archive guarantee. A versioned release or institutional archive still needs to be published.

## Final disposition
- Raw artifact/run-table integrity: PASS.
- Proxy reconstruction against all 18 rows: PASS to floating-point precision.
- Entropy history: recovered and examined; convergence remains PRELIMINARY / NOT CERTIFIED.
- Canonical UMMU scalar screen: encouraging; independent benchmark/model/tally sign-off remains open.
- Numeric physical acceptance limits: not approved.
- CB-PFR superiority: not established; confirmatory comparison remains blocked.
- Winner: none. Full physical validation: not certified.

**Permitted wording:** “We conducted an 18-run C5G7/OpenMC screening campaign across six two-MOX layouts. Direct statepoint review reproduced the exported relative fission-rate proxy to floating-point precision, and source-entropy histories were examined as preliminary convergence diagnostics. Independent benchmark/model/tally sign-off and a preregistered physical acceptance rule remain pending; these results do not yet certify full physical validation or establish CB-PFR superiority over QUBO-only.”
