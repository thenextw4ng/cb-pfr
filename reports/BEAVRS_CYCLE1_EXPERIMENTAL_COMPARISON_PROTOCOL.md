# BEAVRS Cycle 1 day-0 experimental map comparison

**Purpose.** Establish a reproducible first experimental comparison for the CB-PFR / ReactorQ Studio codebase using the public BEAVRS full-core PWR benchmark. This is a physics-model comparison, not yet validation of the CB-PFR ranking method.

## Reproducible execution

- Upstream benchmark repository: https://github.com/mit-crpg/BEAVRS
- Frozen upstream revision: `1ccae04dc3830a5977f08ed7f5f7e1e51ded0d22`
- Upstream OpenMC model generator: `models/openmc/make_beavrs.py` and `models/openmc/beavrs/`
- Experimental observable: Cycle 1 day-0 normalized radial detector map at `measurements/detector_signals/cycle_1/0/radial_measurements_full.csv`
- Experimental state summary: `measurements/detector_signals/cycle_1/0/summary.csv`
- Runner: `scripts/run_beavrs_cycle1_map_validation.py`
- Workflow: `.github/workflows/beavrs-cycle1-map-validation.yml`
- Workflow accepts configurable batch, inactive-batch, and particles-per-batch settings; default is 250 batches, 30 inactive, 2,000 particles/batch.
- Nuclear data: OpenMC official ENDF/B-VII.1 HDF5 library, archive URL pinned in the workflow; the workflow records archive and `cross_sections.xml` SHA-256 hashes.
- Raw run logs, input files, statepoint and comparison outputs are uploaded as a GitHub Actions artifact.

## Observable and comparison method

The BEAVRS day-0 measured map contains 58 instrumented assembly positions. The model runner constructs the full 3-D BEAVRS geometry using the frozen upstream builder, adds a 17×17×1 regular-mesh tally for the fission reaction rate over the active fuel height, extracts the tally bins corresponding to those 58 detector positions, and normalizes the calculated values and measured values separately to mean 1. It then reports:

- normalized-map RMSE and MAE;
- mean absolute relative error;
- Pearson correlation;
- (k_{eff}) and its Monte Carlo standard deviation;
- per-assembly measured/calculated values and residuals;
- statepoint SHA-256 and run settings.

This is a shape comparison of normalized detector measurements and calculated assembly fission rates. It is not absolute-power validation. The benchmark's detector signal and the model's volume-integrated fission-rate tally are related observables but not identical measurement operators; the result must be interpreted as a first comparison, not an exact detector-response calculation.

## Known model-to-measurement mismatch

The Cycle 1 day-0 summary reports average boron 975.25 ppm, inlet coolant temperature 558.875°F, and control-bank withdrawals A/B/C/D/E = 228/228/228/213/230 steps. The upstream model builder's supported default uses nominal 975 ppm, temperature 566.483 K, and bank E at 228 steps withdrawn (its generic RCCA input range is 0–228). The runner uses 975.25 ppm and the closest supported temperature, but records the two-step bank-E mismatch rather than extrapolating the upstream geometry.

Because of this mismatch, and because the initial comparison does not yet propagate the measurement uncertainty or fully model the detector response, **even a favorable numerical result is preliminary evidence, not a complete experimental-validation certificate**.

## Acceptance and interpretation

The script intentionally does not turn arbitrary thresholds into a pass/fail claim. A quantitative result must be reviewed against the benchmark's documented uncertainty and a predeclared, physically justified acceptance rule. Failed convergence, missing detector bins, non-finite values, or missing raw evidence must block any positive claim.

## What this does and does not establish

If the workflow completes successfully, it establishes that a pinned BEAVRS model was run with a named nuclear-data library and compared reproducibly with 58 published detector measurements. It does **not** by itself establish:

1. that the model is validated to all BEAVRS observables or at all operating states;
2. that the legacy CB-PFR burnup-state QUBO maps to the BEAVRS core;
3. that CB-PFR improves selection on a physically meaningful candidate pool;
4. that quantum hardware was used or quantum advantage was demonstrated.

The existing C5G7 assembly-layout study is a separate reformulated benchmark. Its candidates must not be silently identified with BEAVRS states. To validate CB-PFR effectiveness, define a defensible candidate-to-physics map and compare CB-PFR against QUBO-only and other baselines using the same physical evaluation budget.

## Claim wording pending full audit

Appropriate before the run and audit: “A reproducible OpenMC-to-BEAVRS experimental map comparison workflow has been implemented.”

Appropriate only after successful run and artifact review: “An initial BEAVRS Cycle 1 detector-map comparison was performed using the pinned OpenMC model and public measurement data.”

Not supported by this workflow alone: “CB-PFR is fully physically validated,” “CB-PFR improves reactor fuel loading,” or “quantum advantage was demonstrated.”
