# CB-PFR / C5G7 preregistration and gated run plan

**Protocol ID:** `CBPFR-C5G7-PREREG-B0-2026-10-15`  
**Frozen date:** 2026-10-15 (UTC)  
**Purpose:** predeclare analyses and stage gates before confirmatory C5G7 runs.  
**Evidence boundary:** C5G7 supports code-to-reference verification for the canonical case, not experimental validation of the five noncanonical layouts.

## 1. Claim ladder

| Level | Claim | Minimum evidence / gate |
|---|---|---|
| L1 | Software verified | Unit and integration tests; QUBO-energy/constraint properties and fail-closed error tests |
| L2 | Numerical verification against C5G7 reference, canonical UMMU only | B1 pilot passed; B2 independent confirmatory seeds pass scalar screens; B4 pin-power comparison against a reviewed reference |
| L3 | Layout ordering is reproducible and symmetry checked | L2 prerequisites; B3 equivalence TOST for symmetry-related layout pairs; B5 independent transport code comparison |
| L4 | CB-PFR improves selection on physical candidates | L3 prerequisites; B6 expanded layout space, B7 equal-budget selection experiment; report negative results if the superiority endpoint is not met |
| L5 | Experimental validation | Separate B8 toolchain/measurement comparison only; cannot validate ranking of layouts that have no experimental measurements |

C5G7 is a computational benchmark whose reference results are produced by other transport calculations. It is not an experiment. A matching (k_{\mathrm{eff}}) alone does not establish model identity or validate a spatial response.

## 2. B0: predeclared common settings and gates

### Locked design objective and the role of k-effective

For the six-layout and expanded 5 × 5 design studies, the registered exploratory objective is to **minimize the assembly-integrated fission-rate peaking factor**:

\[
F_{\mathrm{fission}} = \frac{\max_a R_a}{\operatorname{mean}_a(R_a)}, \qquad
R_a = \sum_{i \in \text{assembly }a} \bar f_i .
\]

Here \(\bar f_i\) is the mean mesh fission-score tally in mesh bin \(i\), summed over the verified 17 × 17 bin footprint of fuel assembly \(a\). This is a dimensionless relative fission-rate shape proxy—not absolute power, a safety limit, or an experimental measurement. The mesh-to-pin/assembly mapping and tally normalization must be audited before any ranking is treated as more than descriptive.

The C5G7 reference \(k_{\mathrm{eff}} = 1.18655\) is used only for the canonical UMMU code-to-reference check. **It is not automatically an acceptance band for noncanonical layouts.** For the other layouts, record \(k_{\mathrm{eff}}\) and uncertainty as separate responses; do not call the highest- or lowest-\(k\) layout better, safer, or feasible. A design-specific hard physical acceptance band remains **not authorized** until an independent domain reviewer signs off a defensible criterion. B7 must therefore limit its primary endpoint to selecting the best candidate under the registered \(F_{\mathrm{fission}}\) objective, unless a later versioned amendment registers additional physically justified hard constraints before those results are inspected.

### Model identity and common run conditions

- Reference source: `mit-crpg/benchmarks`, pinned commit `ba41bee54320ada0b4ac39a0dd2ca3c1d090a450`.
- OpenMC version: 0.16.0.
- Required C5G7 seven-group boundaries (eV): `[1e-5, 0.0635, 10, 100, 1000, 500000, 1000000, 20000000]`.
- Entropy mesh: 51 × 51 in x/y, bounds [-32.14, 32.14] in each axis; zero source-outside-mesh warnings required.
- Statepoints, XML, logs, source-convergence traces, seeds, and hashes must be archived per run.
- Seeds used in B1 are pilot-only and may not be reused in B2. Earlier runs from before the corrected entropy mesh / standard-group-structure audit are not pooled into the B2 confirmatory sample.

### B1 pilot (screening only)

Total-batch profile: 7,000 batches, 10,000 particles/batch, one thread.

**Source-start sensitivity: 12 runs**
- Initial source profiles: `baseline_all_fuel`, `left_column_only`, `right_column_only`, `upper_row_only`.
- Three paired seed values: 810001, 810002, 810003.
- Fixed inactive batches: 500.
- The source boxes are restricted to fissionable material. They describe only the initial source distribution; they do not constrain the later converged eigenvalue source.

**Inactive-batch sweep: 12 runs**
- Inactive batches: 100, 300, 500, 1000.
- Three paired seed values: 820001, 820002, 820003.
- Baseline source profile: `baseline_all_fuel`.
- Total batches and particles/batch stay fixed, so increasing inactive batches trades active statistical samples for source relaxation.

**B1 predeclared screens**
1. All 24 runs must finish and have passing raw-HDF5 checks, correct standard group boundaries, unique statepoint hashes, correct seed/settings correspondence, non-empty entropy and (k\)-generation traces, and zero entropy-mesh warnings.
2. An inactive profile is eligible only if, for each of its three pilot seeds, the absolute active-trace second-half minus first-half (k\)-generation mean is ≤ 25 pcm, and the absolute last-quarter minus first-quarter entropy mean is ≤ 0.01 nat.
3. Choose the **smallest** eligible inactive count to preserve active batches. If none is eligible, B1 is inconclusive: extend the pilot at a higher total-batch count under a versioned amendment; do not launch B2.
4. For each non-baseline initial source profile, compare (k_{\mathrm{eff}}) to `baseline_all_fuel` using the same seed in paired runs. The 90% paired Student-t confidence interval (df = 2) for each mean difference must lie wholly within ±25 pcm (TOST equivalence screen). If it fails, the source-start robustness gate is inconclusive and the pilot must be extended; do not launch B2.
5. If the selected inactive count is not 500, repeat the four source-profile conditions at that selected inactive count with three fresh paired seeds before B1 can pass.
6. The pilot selects settings only. It provides no confirmatory benchmark claim.

### B2 confirmatory canonical UMMU

- Ten **new** seeds: 8200001–8200010; no seed is shared with B1 or earlier pre-correction runs.
- Batch/inactive/particle settings are locked to the B1 recommendation. If B1 chooses 7,000 batches, retain that profile; if B1 fails the 7,000-batch drift screen, B1 must be extended and amended before this gate.
- Reference: (k_{\mathrm{eff}} = 1.18655\), reference standard uncertainty 0.000095.
- Scalar screen: (|\Delta k| \le 100\) pcm and (|z| \le 2\), using the predeclared combined uncertainty.
- Between-seed / within-run SD ratio screen: 0.55–1.45, i.e. the rounded 95% chi-square interval for the ratio of a sample standard deviation based on n = 10 to the common within-run SD (df = 9). Report the actual ratio, not just pass/fail.
- The ten B2 replicates are a new confirmatory sample. Do not pool with B1 or runs with a different mesh/model configuration.
- Source convergence must be reviewed from full batch-wise traces. No scalar-only auto-certification.

### B4 canonical pin-power comparison

Reuse B2 statepoints; no extra transport run is planned initially. Extract an official, benchmark-compatible reference pin-power table from the primary specification/supplement, review the orientation and normalization, then compare all compatible pin bins with AVG, RMS relative error and maximum absolute relative error with an uncertainty statement. The 51 × 51 mesh is not presumed pin-aligned until index mapping, dimensions and tally integration are independently checked. If the official pin-power data cannot be obtained or matched, B4 stays blocked and L2 is not claimed.

### B3 six-layout symmetry/repeatability (only after B2 passes)

- Six layouts × 10 seed replicates = 60 runs under one common frozen profile.
- Test the preregistered mirror-equivalent pairs `MMUU ↔ MUMU` and `UMUM ↔ UUMM` using two one-sided tests (TOST) and a 90% CI; equivalence margin ±12 pcm.
- Report all six run means, within-run uncertainty, between-seed SD, pairwise CI, and statepoint/hash checks.
- A failed or inconclusive TOST is not evidence of symmetry. Do not launch B3 unless B2 passes its preregistered gates.

### B5 cross-code comparison (only after B3)

- Canonical UMMU plus three preregistered layouts in a second independent transport code.
- Match geometry/material definitions, seven-group boundaries, cross-section provenance and tally definitions as closely as the second code permits. If the code or library cannot be installed/licensed or same-data equivalence cannot be demonstrated, record B5 as blocked, not passed.
- Compare (k_{\mathrm{eff}}), compatible spatial response, and layout ordering with uncertainties. Agreement of rank alone is insufficient.

### B6 expanded 5 × 5 design (only after B5)

- Outer reflector row/column fixed; interior 3 × 3 fuel block; exactly four MOX and five UO₂ positions: (\binom{9}{4}=126) raw assignments.
- Recompute symmetry classes under the **actual** boundary conditions and position mapping. The 23-class count is only the full D4-symmetry hypothesis and must not be reused if mixed boundary conditions break those transformations.
- Initial high-budget truth runs target five independent seeds per verified symmetry class at 7,000 batches only if a convergence pilot for the 5 × 5 model passes; otherwise do not call the reduced budget converged.

### B7 equal-budget selection experiment (only after B6)

Compare random selection, point-estimate, uniform-margin, equal-allocation R&S, adaptive/OCBA, and CB-PFR. Freeze the candidate pool, selection endpoint, evaluation budget, failure handling, and pairing before outcomes are revealed. Endpoint: probability of selecting the true best under the registered objective and regret (F\); uncertainty from paired pool-level bootstrap intervals.

**Accounting correction:** 690 OpenMC runs total do not by themselves give every one of seven methods an independent equal-budget allocation. To compare seven allocation policies fairly, either reuse a separately generated shared observation cube for non-adaptive policies while explicitly restricting the claim, or budget 690 per policy (4,830 run-policy observations) with a frozen truth definition. The final B7 workload must be amended and signed off before execution. Inactive=10 / 100-batch stress profiles are explicitly smoke tests and may carry source-convergence bias; they cannot be treated as physical truth or validated uncertainty.

### B8 experimental comparison

BEAVRS registration/orientation must be independently audited or a suitable KRITZ-2 measurement/reference case selected. B8 checks the toolchain against experimental reference quantities. It does not validate the ranking of unmeasured six-layout variants.

## 3. Stage gate and no-result rules

Run order: **B0 → B1 → B2 and B4 → B3 → B5 → B6 → B7**. B8 is a parallel toolchain validation track with its own specification review, never evidence of layout ranking.

- A failed gate stops downstream confirmatory runs until a versioned amendment is signed.
- Do not restart or rerun solely because results are inconvenient. Reruns are permitted only for documented infrastructure failure, input/hash mismatch, or a preregistered extension rule.
- All exclusions, failed jobs, inconclusive results, and negative selection outcomes stay in the dossier.
- Thresholds and selected seeds cannot be edited after viewing confirmatory outcomes.
- This protocol does not authorize a claim of official benchmark acceptance, experimental validation of layout ranking, reactor-safety benefit, quantum advantage, or physical superiority of CB-PFR.

## 4. Evidence to release

The campaign release must contain the frozen protocol and SHA-256, upstream commit, all input/output hashes, per-run audits, source traces, raw statepoints, aggregation code, machine-readable results, CI logs, and an evidence-bounded claims matrix. A separate reviewer must sign the model-identity gate before the paper claims benchmark verification.

## References

1. OECD/NEA, *Benchmark on Deterministic Transport Calculations Without Spatial Homogenisation*. https://www.oecd-nea.org/jcms/pl_13548/benchmark-on-deterministic-transport-calculations-without-spatial-homogenisation
2. C5G7 2D/3D MOX benchmark specification and reference: https://doi.org/10.1016/j.pnueene.2004.09.003
3. Pinned OpenMC implementation: https://github.com/mit-crpg/benchmarks/tree/ba41bee54320ada0b4ac39a0dd2ca3c1d090a450
