# CB-PFR C5G7 — Full Raw Trace Diagnostics

**Date:** 2026-10-12  
**Input:** 18 raw OpenMC `statepoint.7000.h5` files from the high-budget confirmation artifact.  
**Scope:** post-inactive generation history only; this is a diagnostic, not a convergence certification.

## Method

- Read `entropy` and `k_generation` arrays directly from each statepoint; verified `n_inactive` from the same file and excluded the first inactive batches from descriptive summaries.
- Calculated mean, sample standard deviation, linear slope per 1,000 batches, naive OLS slope p-value, first-vs-last active-trace quartile shift, lag-1 autocorrelation, and 500-batch block-mean SD.
- Generated an accompanying local figure from non-overlapping 100-batch means to make long-run patterns visible.
- The naive OLS p-value is **not** treated as a valid formal test because serial dependence is present, particularly for entropy. No universal pass/fail threshold was specified before inspecting these data.

## Results

- Statepoints analyzed: **18** (6 layouts × 3 independent runs).
- Entropy first-to-last quartile shift: median **-7.56826e-05**, maximum absolute **0.00311352**.
- Entropy linear slope per 1,000 active batches: median **3.25841e-05**, maximum absolute **0.000690828**.
- Entropy lag-1 autocorrelation: median **0.630**, range **0.554–0.720**.
- `k_generation` first-to-last quartile shift: median **0.000223669**, maximum absolute **0.00116035**.
- `k_generation` linear slope per 1,000 active batches: median **4.70653e-05**, maximum absolute **0.000210298**.
- `k_generation` lag-1 autocorrelation: median **0.019**, range **-0.011–0.047**.

## Interpretation and limitations

The `k_generation` trace shows low lag-1 correlation and small descriptive first/last-quartile shifts in this set, while entropy has materially higher lag-1 autocorrelation (median about 0.63). This is a reason not to interpret raw per-batch points as independent samples. The summary does not show one uniform direction of drift across all runs, but absence of a common drift is not proof of source convergence.

The analysis is **not a convergence certificate**: thresholds were not predeclared; no chain mixing or effective-sample-size criterion was registered; an inactive-generation sensitivity comparison has not been executed; and no independent reviewer has signed off on the source-convergence protocol. The appropriate status remains `DIAGNOSTIC_REVIEW_REQUIRED`, not `PASS`.

## Required follow-up

1. Predeclare entropy and eigenvalue/source-stability acceptance criteria with a defensible rationale before re-running/inspecting the sensitivity results.
2. On at least one representative layout and one contrasting layout, run longer inactive/source-start sensitivity cases using fixed model, cross-section, particle-count, and seed protocol; compare k-effective and spatial tallies with uncertainty.
3. Report uncertainty/covariance treatment, trace diagnostics, and all failed/inconclusive runs. Do not claim physical validity or optimizer superiority from this trace review alone.

## Numeric artifacts

The run-level CSV is attached to the technical closeout package generated on 2026-10-12. The local plot uses 100-batch means for all 18 traces.