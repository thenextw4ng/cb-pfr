# CB-PFR four-gate scientific closeout protocol

**Status as of 2026-10-12: IN PROGRESS — no physical-validation certification and no superiority claim.**

This protocol closes the four workstreams without inventing thresholds or changing a rule after seeing results. The target claim is whether CB-PFR's post-optimization selection layer adds measurable value over the four-variable material-placement QUBO and simple baselines. It does not target reactor-safety certification or quantum advantage.

## Gate 1 — Model and tally audit

### Evidence currently available
- The archived six-layout campaign contains 18 completed OpenMC runs: six layouts × three seed rounds. Each row has a unique seed and statepoint SHA-256; a single MGXS hash; common run settings; and a passing seven-group boundary audit.
- Layouts: `MMUU`, `MUMU`, `MUUM`, `UMMU`, `UMUM`, `UUMM`; exactly two MOX and two UO2 per layout. Five reflector positions remain fixed in the source design manifest.
- The tally mesh is 51 × 51 over 64.26 cm, i.e. 1.26 cm per bin; the assembly reducer groups 17 × 17 bins. This is internally consistent with stated 17 × 17 pin/pitch dimensions, but does not prove correct cell/material assignment or tally mapping.
- The exported proxy is `max(assembly-integrated fission rate) / mean(assembly-integrated fission rate)`. It is a dimensionless relative fission-rate proxy—not absolute power in watts and not a safety limit.
- Canonical UMMU saved-statepoint screen: mean `k_eff = 1.1864932118`, difference `−5.6788 pcm` from project reference `1.186550`, combined-uncertainty z `−0.4342`; normalized spatial-shape maximum absolute relative difference `0.1790%` against the selected four-position reference.

### What remains open
This is an internal provenance/numerical screen, not independent benchmark validation. An independent reviewer must compare generated geometry, materials, boundary conditions, group constants, tally regions and normalization with the applicable primary C5G7 specification and verify that the reference observable is commensurate with the OpenMC tally. The reference uncertainty covariance was not available for the prior exploratory propagation; its independence assumption is not definitive.

Convergence is separate. Canonical UMMU traces received an internal qualitative inspection and showed no obvious persistent drift, but trend tests are exploratory, and one layout cannot certify all six. OpenMC guidance notes that `k_eff` can appear stable before the spatial fission source converges; Shannon entropy is a useful diagnostic, not universal proof: https://docs.openmc.org/en/stable/usersguide/settings.html.

**Gate 1 disposition:** exported-table integrity checks pass; independent model/tally sign-off and six-layout convergence review remain open.

## Gate 2 — Frozen fail-closed physical decision rule

1. No candidate is physically accepted until independent model/tally review is recorded.
2. Physical metrics and tolerances must be sourced from the applicable benchmark specification or justified prospectively for this exact model and research question. No threshold is inferred from observed candidate results.
3. Label each metric correctly: `k_eff`, normalized fission-rate shape, assembly power, or another observable. Do not silently interchange them.
4. Report within-run Monte Carlo uncertainty separately from between-seed variability and reference uncertainty; state covariance assumptions.
5. A candidate must pass every predeclared criterion. If a criterion is absent, incomparable, or unreviewed, return `NO_SELECTION / INCONCLUSIVE`.
6. Preserve all candidates and failures. Post-result threshold/weight changes must be versioned as exploratory and require a new independent holdout for confirmatory claims.

The machine-readable decision-rule template is deliberately not approved and contains no fabricated tolerances.

## Gate 3 — Fair comparison: CB-PFR vs QUBO-only and simple baselines

### Formulations must not be conflated
The four-variable material-placement QUBO is `E(y) = A (sum_i y_i − 2)^2`, where `y_i=1` means MOX and `0` means UO2. All six feasible exactly-two-MOX layouts have the same energy (zero, apart from a common offset). This formulation enforces composition but cannot rank the six layouts. The selector QUBO is constructed **after** physical evidence is ingested; its score cannot be retroactively called the pre-physics QUBO objective.

Thus, the current artifact does not identify a numerical CB-PFR-vs-QUBO-only winner. Inventing QUBO scores or treating post-physics selector energy as QUBO-only performance would be invalid.

### Confirmatory protocol after prerequisites are met
- Freeze candidate set, source/model hashes, physical acceptance rule, CB-PFR scoring/weights, and baseline definitions before opening held-out results.
- Compare at minimum: (a) CB-PFR physical-feedback selection; (b) actual pre-physics QUBO output with its tie policy specified; (c) seeded random selection; and (d) a simple non-quantum ranking/search baseline using the same information budget.
- Use identical candidate sets and equal transport-evaluation budgets. Count all runs and failed/infeasible evaluations; report wall-clock/CPU cost and transport calls.
- Use prospective independent seed rounds or new runs not used to tune CB-PFR. Three existing rounds support exploratory stability only.
- Predeclare primary endpoints, e.g. fraction passing the accepted physical rule and best accepted objective under a fixed budget. Secondary endpoints can include uncertainty, selection regret, ranking stability and compute cost.
- Report uncertainty intervals where supported. Preserve ties, inconclusive results, and outcomes favoring a baseline.

### Existing-data result (exploratory only)
Leave-one-seed-round-out analysis selected the lowest mean fission-rate proxy on two rounds. It chose `MMUU` in all three folds; `MMUU` also had the lowest proxy in each held-out round. This is descriptive proxy-ranking stability, not independent physical validation or CB-PFR superiority: only three rounds exist, and the same proxy is used for selection and evaluation.

**Gate 3 disposition:** comparison is BLOCKED / NOT IDENTIFIABLE. The pre-physics QUBO has no ranking signal across feasible layouts; no approved physical rule or prospective holdout exists.

## Gate 4 — Reproducibility freeze

Preserve the original raw workflow artifact, exported run-level CSV, audit JSONs, code, environment/command record and SHA-256 manifest. Copy the raw artifact to a durable release/archive before GitHub Actions retention expires, then re-hash the downloaded copy. The evidence bundle is a frozen snapshot, not a physical-validity certificate.

## Current disposition
- Software/data integrity: PASS for the audited run-level table and recorded hashes.
- Internal geometry/tally consistency: PARTIAL; mesh dimensions are consistent, independent specification-to-model/tally sign-off is open.
- Canonical scalar and normalized spatial screen: PASS as project-level numerical screening only.
- Source convergence: internal qualitative review exists for canonical UMMU; six-layout certification is OPEN.
- Physical decision rule: fail-closed rule frozen; numerical criteria await independent evidence-based approval.
- CB-PFR superiority: NOT ESTABLISHED; fair comparison BLOCKED / NOT IDENTIFIABLE.
- Winner: NONE.
- Physical validation: NOT CERTIFIED.

## Release language permitted now
“CB-PFR was evaluated in a reproducible six-layout C5G7/OpenMC computational screening study. Run provenance and selected numerical consistency checks passed. Independent benchmark/model/tally review and complete convergence/acceptance review remain pending; the study does not yet establish full physical validation or superiority over QUBO-only.”
