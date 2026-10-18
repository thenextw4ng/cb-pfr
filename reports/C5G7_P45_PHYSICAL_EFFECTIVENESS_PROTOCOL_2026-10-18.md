# C5G7 P-4/P-5/P-6 physical-effectiveness pilot protocol

**Protocol date:** 2026-10-18  
**Status:** registered in GitHub Actions; exploratory, not an official benchmark-acceptance protocol.

## Question

Does the candidate chosen by the CB-PFR risk-adjusted ranking have a lower independently evaluated assembly-integrated fission-rate peaking proxy than candidates chosen by a point estimate and transparent baselines, under a fixed six-layout C5G7 design space?

This is a test of one *new C5G7 UO2/MOX assembly-placement formulation*. It is not a validation of the legacy `fresh / once_burned / twice_burned` QUBO mapping.

## P-4 — independent intermediate-budget screening

- Six enumerated layouts: MMUU, MUMU, MUUM, UMMU, UMUM, UUMM.
- Three independent seeds per layout; 18 runs.
- OpenMC 0.16.0; 2,000 batches, 100 inactive, 5,000 particles/batch, one thread.
- Seed bases: 810000, 820000, 830000, with a deterministic layout offset.
- Outputs: raw HDF5 audit, full statepoint hash, (k_{eff}) and within-run SD, generation/entropy traces, and assembly-integrated fission-rate peaking proxy.

P-4 is the screening pool. No candidate is physically declared acceptable solely from P-4.

## P-5 — independent high-budget held-out evaluation

- The same six layouts, each run on three new independent seeds; 18 runs.
- OpenMC 0.16.0; 20,000 batches, 500 inactive, 10,000 particles/batch, one thread.
- Seed bases: 910000, 920000, 930000, separate from all P-4 seed bases and the earlier P-1/P-2/P-3 pilot.
- Same model revision, MGXS group boundaries, geometry/material definitions and tally specification as P-4.

P-5 is held out from method selection. P-4 ranking rules are frozen in this protocol and do not use P-5 data to choose a layout.

## P-6 — held-out method comparison

1. Point estimate chooses the layout with the smallest P-4 mean peaking proxy.
2. CB-PFR chooses the layout with the smallest `mean P4 proxy + 1.0 × between-seed SD(P4 proxy)`. This is a declared operational risk score, not a calibrated confidence bound.
3. Uniform-margin baseline adds the same constant margin to all P-4 candidate scores. For a single unconstrained scalar objective this mathematically preserves the point-estimate ranking; it is included as an implementation sanity check, not an independent stronger baseline.
4. The material-count-only QUBO gives every exactly-two-MOX layout equal energy. Its feasible output is therefore treated as uniform random selection absent a separately justified physics objective. A random feasible baseline is also sampled.
5. Score each selected layout only against P-5 data. Report observed held-out regret relative to the lowest observed P-5 layout mean and paired bootstrap distributions, including the full uncertainty interval and selection frequencies.

The bootstrap (10,000 resamples; seed 20261018) is an exploratory resampling analysis with only three independent seeds per layout. It is not a substitute for multiple independent screening/held-out cohorts. A finding counts as an initial signal only if the CB-PFR-minus-point-estimate regret is consistently below zero and its uncertainty interval excludes zero; even then the claim is limited to this design space, objective, model and pilot.

## Integrity and analysis gates

- Exactly 18 completed run records for P-4 and 18 for P-5.
- Three records for each layout in each phase.
- Raw HDF5 settings/scalar/tally audits pass, standard C5G7 seven-group boundaries pass, and all statepoint hashes are present and unique.
- Identical MGXS data identity across the campaign is checked.
- Record within-run Monte Carlo uncertainty separately from between-seed variability.
- Preserve batch-wise (k)-generation and entropy diagnostics; `DIAGNOSTIC_REVIEW_REQUIRED` stays an open review state, never a pass label.
- A successful integrity gate does not certify convergence, benchmark fidelity or physical acceptability.

## Physical-claim boundary

A design-specific acceptable (k_{eff}) band has not been approved for the six noncanonical layouts. Until that band has a defensible basis and the canonical model/tally mapping has undergone independent review, P-6 compares only the **relative fission-rate-shape proxy**. The proxy is not absolute power and is not a safety metric. The report cannot establish a physically feasible/safe design or a general CB-PFR advantage.

The canonical UMMU case remains the reference-identity check. A close (k_{eff}) match alone cannot validate geometry, materials, boundary conditions, nuclear-data identity or spatial response. Passing the project screens is not official OECD/NEA acceptance.

## Workflow and artifacts

Workflow: `.github/workflows/c5g7-p45-physical-effectiveness.yml`  
Analyzer: `scripts/analyze_c5g7_p45_physical_effectiveness.py`  
Artifacts contain per-run `STUDY_SUMMARY.json`, `CASE_RESULT.json`, OpenMC logs, statepoints, audits, source diagnostics and tally-derived proxy outputs. The aggregate artifact includes CSV and JSON audit plus a human-readable report.

## Allowed wording if the evidence gate passes

> An exploratory 36-run C5G7 campaign compared the CB-PFR risk-adjusted selection with point-estimate and selection baselines using independent higher-budget OpenMC estimates of a relative fission-rate-shape proxy. This is evidence about the declared six-layout model and pilot protocol only; physical feasibility, benchmark acceptance and generalizable CB-PFR superiority remain unestablished unless additional acceptance and replication gates are independently satisfied.
