# CB-PFR vs QUBO-only: direct evidence comparison (2026-10-12)

## Executive result

**No confirmatory superiority claim is supported yet.** The current composition-only QUBO enforces two MOX assemblies but assigns the same energy to all six two-MOX layouts. It therefore has zero ranking power among the candidates. CB-PFR's post-physics selector is the only one of the two that has, in the current exploratory analysis, used physical proxy observations to rank layouts. That is a *functional distinction*, not yet proof of a reliable physical-performance advantage.

## Evidence used

- GitHub Actions high-budget run 38229045726; three seed rounds, six layouts (18 OpenMC statepoints).
- Raw statepoint reconstruction reproduced the exported relative assembly-integrated fission-rate peaking proxy with maximum absolute discrepancy 2.22e-16.
- Proxy is a relative fission-rate peaking indicator, **not** absolute power, a safety limit, or by itself a physical acceptance criterion.
- The composition objective is A*(sum(y_i)-2)^2. Every layout in this candidate set has exactly two MOX assemblies, so all six tie under this objective.

## Layout-level descriptive results

| Layout | Mean k-effective | Mean fission-rate peaking proxy | Interpretation |
|---|---:|---:|---|
| MMUU | 1.1436721 | 1.2953689 | Lowest observed proxy |
| MUMU | 1.1437002 | 1.2963641 | Proxy ~0.0009953 above MMUU |
| MUUM | 1.1562627 | 1.3161492 | Higher proxy than MMUU/MUMU |
| UMMU | 1.1864986 | 1.8671004 | Canonical reference arrangement; scalar k-effective screen near saved reference |
| UMUM | 1.2046883 | 1.8167198 | Lower proxy than UMMU, but not lowest |
| UUMM | 1.2046416 | 1.8160915 | Lower proxy than UMMU, but not lowest |

The (k_{eff}) values vary substantially by arrangement; these results should not be interpreted as a simple ranking where larger or smaller is automatically better. Physical meaning and admissibility must be defined for the study's intended reactor state and benchmark. The canonical UMMU mean is about -5.14 pcm from the saved scalar reference 1.186550; this is an encouraging scalar screen only, not complete validation.

## Head-to-head algorithm comparison

### A. Composition-only QUBO
- Objective: (A(\sum_i y_i-2)^2).
- Result for this six-candidate set: **six-way tie**.
- What it can claim: enforces the requested MOX count.
- What it cannot claim: selecting the physically best layout, reducing peaking, or improving reliability.

### B. CB-PFR post-physics selector (exploratory)
- Leave-one-seed-round-out selection chose MMUU in all 3 folds.
- Observed held-out proxy regret: 0 across those three folds.
- Uniform-random selection has expected proxy regret around 0.272 on the same proxy scale in the existing exploratory calculation.
- This suggests CB-PFR's physical-proxy-informed ranking can be more informative than a tie/random choice on this tiny candidate set. It does **not** prove a generalization advantage: there are only three seed rounds, six layouts, and no preregistered physical acceptance rule or untouched confirmation set.

## What would count as a real CB-PFR advantage?

A confirmatory test must be frozen *before* the new results are inspected:

1. Lock the six candidates, geometry/material/MGXS hashes, OpenMC version and settings.
2. Lock the primary endpoint(s), physical acceptance criteria, uncertainty handling, CB-PFR weights, and tie policy. Do not tune them on the confirmation runs.
3. Compare CB-PFR with (i) composition-only QUBO plus a predeclared tie-break/random policy and (ii) any genuine pre-physics optimizer only if its objective actually ranks the layouts.
4. Use equal physical-evaluation budgets and new independent seed rounds. Preserve every run, including failures.
5. Report selection regret, probability of meeting the physical acceptance rule, variability across rounds, computational cost, and uncertainty. Keep source convergence and independent model/tally review as separate gates.

## Current decision

- **Demonstrated:** current QUBO composition objective cannot rank the six candidates; CB-PFR's post-physics proxy ranking has a useful exploratory signal; raw tally extraction is reproducible.
- **Not demonstrated:** statistically reliable physical advantage, safety superiority, full physical validation, or generalization beyond these six candidates and three seed rounds.
- **No winner is certified.** If the research question is which layout minimizes the current proxy, MMUU is the exploratory proxy winner. It must not be called the physically optimal or safest layout until the physical rule and independent validation are approved.

## Source artifact and reproducibility

Raw artifact: [GitHub Actions run 38229045726](https://github.com/thenextw4ng/cb-pfr/actions/runs/38229045726)  
Raw statepoint audit: [CBPFR_RAW_STATEPOINT_AUDIT_2026-10-12.md](CBPFR_RAW_STATEPOINT_AUDIT_2026-10-12.md)  
Trace diagnostics: [CBPFR_C5G7_FULL_TRACE_DIAGNOSTICS_2026-10-12.md](CBPFR_C5G7_FULL_TRACE_DIAGNOSTICS_2026-10-12.md)

