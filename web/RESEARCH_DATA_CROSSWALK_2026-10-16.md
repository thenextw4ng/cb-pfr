# HTML Workstation — Research Evidence Crosswalk

**Snapshot date:** 2026-10-16  
**Purpose:** Reconcile the browser dashboard with the revised CB-PFR methods paper and the most recent C5G7/OpenMC policy-replay evidence.  
**Rule:** Synthetic method evidence, neutron-transport observations, data-integrity checks, and physical-validation claims remain separate.

## 1. Workstation files

- `index.html` — dashboard structure and evidence sections.
- `styles.css` — local responsive styling; no missing root-level stylesheet dependency.
- `app.js` — interactive charts, layout selector, provenance messages, and paper tables.
- `research_snapshot.json` — versioned source values used by the view. It is an aggregate snapshot, not the raw 1,200-run table.

## 2. Revised method paper ingested

**Title:** *CB-PFR: An Auditable Selection Layer for Noisy Optimization Candidates, with a Calibration Protocol and an Explicit Operating Envelope*  
**Source file supplied in the conversation:** `CBPFR_ICIMCIS_revised(2).pdf`  
**SHA-256:** `55645d738af26bfe9d4ad9eae4ca8f7ab2c83f02da36e6f4ca825e7d9c34ac9b`  
**Length:** 6 pages.

The dashboard transcribes T7 Table III (8 regimes; 20,000 synthetic test pools per regime), the paired matched-95%-feasibility differences from Table IV, and H1–H4 from Table V. The values are held in `research_snapshot.json` and shown with their source and claim boundary.

Key interpretation from the supplied paper:

- At fixed (z=1), the truly feasible selection rate rises over point-estimate ranking, but the primary feasible-and-near-optimal endpoint is lower in six of eight regimes.
- When both rules are tuned for the primary endpoint, CB-PFR is within about one percentage point of the uniform-margin baseline.
- At matched 95% feasibility, the reported gain over uniform margin depends on the regime; it ties under homogeneous uncertainty and loses in the coupled regime.
- Adaptive allocation raises the primary endpoint by about 8–19 percentage points in seven of eight regimes, making evaluation allocation a more consequential choice in this experiment.
- Self-calibration restores arbitrary-candidate bound coverage from 88.0% to 97.3% against 97.5% nominal, while selected-candidate coverage remains below nominal.
- The paper itself says T7 is synthetic, self-registered in one working session without an independent timestamp, not independently replicated, and that the matched-feasibility T7b analysis is post hoc.

This repository snapshot records the attached PDF's SHA-256 for identity. The exact PDF binary itself is **not** embedded in the HTML bundle; the dashboard shows the transcribed tables plus the fingerprint so they can be reconciled with the supplied file.

## 3. Synthetic benchmark evidence kept distinct

### T2

- 40,000 pools across four synthetic scenarios.
- Pooled feasible-selection gain: +0.4875 percentage points versus point estimate and uniform margin.
- Paired 95% intervals are around +0.37 to +0.60 points.
- The prespecified practical-effect threshold was at least +2 points, so the rule was **not met**.

Source: [confirmatory result report](https://github.com/thenextw4ng/cb-pfr/blob/research/fixed-budget-ranking-selection-benchmark/reports/CB_PFR_RS_SYNTHETIC_CONFIRMATORY_RESULTS_2026-10-11.md).

### T3

- 6,000 pools across six regimes.
- CB-PFR outperforms point estimate in the three calibrated regimes but does not beat the development-tuned uniform-margin baseline in all primary regimes.
- Decision: the prespecified synthetic superiority gate was not met.

Source: [effectiveness benchmark report](https://github.com/thenextw4ng/cb-pfr/blob/research/cbpfr-effectiveness-benchmark-20261015/reports/cbpfr_effectiveness_benchmark_2026-10-15.md).

## 4. Latest C5G7/OpenMC campaign and equal-budget replay

**Study:** `CBPFR-C5G7-equal-budget-policy-replay-2026-10-16`  
**Successful workflow:** [GitHub Actions run 38853860378](https://github.com/thenextw4ng/cb-pfr/actions/runs/38853860378)  
**Archived replay artifact ID:** `12025659920`  
**Source branch:** `research/c5g7-b0-prereg-b1-pilot-20261015`.

The archived outputs inspected for this snapshot reported:

- 1,200 low-budget V2a observations (200 common seed pools × six layout labels) at 800 batches, 500 inactive batches, 2,000 particles per batch, one thread.
- 60 high-budget reference runs (10 per layout) at 10,000 batches, 1,000 inactive batches, 10,000 particles per batch, one thread.
- Unique statepoint hashes, one shared MGXS hash, a passed seed-ledger/integrity audit, and complete six-layout pool coverage.
- An offline replay with 60 calibration pools, 140 held-out pools, 28 reported decision blocks, and the same 18-evaluation budget per block. The replay launched zero new OpenMC runs.

Recorded policy results:

| Policy | Empirical-best match rate | Mean empirical regret in (F_{fission}) |
|---|---:|---:|
| Adaptive R&S, equal budget | 50.0% | 0.0005467 |
| CB-PFR relative screen | 32.1% | 0.0007420 |
| Point estimate, equal allocation | 32.1% | 0.0007420 |
| Uniform margin, equal allocation | 32.1% | 0.0007420 |

Interpretation boundary: the empirical reference is the mean of high-budget model results under the replay's declared replicate split. It is noisy, not exact physical truth. All low-budget V2a records remain flagged for convergence diagnostics; the aggregate summary explicitly says `convergence_certified=false`. This result does not demonstrate that the model is converged, officially accepted against C5G7, or experimentally validated against a reactor.

The earlier [V2a inventory audit](https://github.com/thenextw4ng/cb-pfr/blob/research/c5g7-b0-prereg-b1-pilot-20261015/reports/C5G7_V2A_ARTIFACT_INVENTORY_AUDIT_2026-10-16.md) predates the successful final replay and marks the analysis pending. The later successful replay workflow is the authority for the policy-analysis completion status; the earlier report remains useful for its artifact-count details.

Protocol: [CB-PFR/C5G7 convergence, selection and QUBO protocol](https://github.com/thenextw4ng/cb-pfr/blob/research/c5g7-b0-prereg-b1-pilot-20261015/docs/experiments/CBPFR_C5G7_CONVERGENCE_SELECTION_QUBO_PROTOCOL_2026-10-16.md).

## 5. Values displayed for the V2a campaign

The chart's six layout means are run-level descriptive summaries of the 200 low-budget observations per layout. Error bars show the observed between-run standard deviation of the derived proxy. They are not validated uncertainty bounds and do not replace source convergence checks.

The high-budget reference means are shown as empirical ranking references. The displayed lowest-mean label must not be called a physically optimal or safe fuel layout. In particular, the QUBO composition penalty has equal energy for all six exact-two-MOX layouts; it cannot rank their physical responses by itself.

## 6. Claim guardrails in this workstation

Supported within the displayed scope:

- CB-PFR is an implemented, auditable, deterministic post-optimization ranking/screening method.
- T2/T3/T7 characterize its synthetic operating envelope, including failed or mixed hypotheses.
- A matched-pool C5G7/OpenMC data-integrity audit and an equal-budget offline selection-policy replay were completed.

Not established:

- Source/eigenvalue convergence for the full current campaign.
- Official C5G7 benchmark acceptance, experimental reactor validation, or reactor safety.
- A physically optimal fuel layout or physical superiority of CB-PFR.
- General CB-PFR superiority over equal-allocation baselines on the current C5G7 data.
- Quantum-hardware execution or quantum advantage.

## 7. Run the HTML workstation

From the repository's `web/` directory:

```bash
python3 -m http.server 8000
```

Open `http://localhost:8000/`. The page loads `research_snapshot.json` over HTTP; opening the HTML directly with a `file://` URL may block that request. The UI does not run OpenMC. It plots the versioned snapshot and intentionally leaves position-wise mesh/geometry views unpopulated when raw browser-ready arrays/XML are absent.
