# BEAVRS Cycle 1 day-0 experimental map comparison

**Purpose.** Establish a reproducible first experimental comparison for the CB-PFR / ReactorQ Studio codebase using the public BEAVRS full-core PWR benchmark. This is a physics-model comparison, not yet validation of the CB-PFR ranking method.

## Reproducible execution

- Upstream benchmark repository: https://github.com/mit-crpg/BEAVRS
- Frozen upstream revision: `1ccae04dc3830a5977f08ed7f5f7e1e51ded0d22`
- Upstream OpenMC model generator: `models/openmc/make_beavrs.py` and `models/openmc/beavrs/`
- Experimental observable: Cycle 1 day-0 tilt-corrected radial map at `measurements/detector_signals/cycle_1/0/radial_measurements_full_tc.csv`, restricted to the 58 instrumented labels identified by `radial_measurements_full.csv`
- Experimental state summary: `measurements/detector_signals/cycle_1/0/summary.csv`
- Runner: `scripts/run_beavrs_cycle1_map_validation.py`
- Coordinate crosswalk export: `beavrs_coordinate_crosswalk.csv` (193 assembly rows; 58 instrumented detector rows; SHA-256 recorded in the run manifest)
- Workflow: `.github/workflows/beavrs-cycle1-map-validation.yml`
- Workflow accepts configurable batch, inactive-batch, and particles-per-batch settings; default is 500 batches, 50 inactive, 3,000 particles/batch.
- Nuclear data: OpenMC official ENDF/B-VII.1 HDF5 library, archive URL pinned in the workflow; the workflow records archive and `cross_sections.xml` SHA-256 hashes.
- Raw run logs, input files, statepoint and comparison outputs are uploaded as a GitHub Actions artifact.

## Observable and comparison method

The BEAVRS day-0 measured map contains 58 instrumented assembly positions. The model runner constructs the full 3-D BEAVRS geometry using the frozen upstream builder, adds a 15×15×1 regular-mesh tally for the U-235 fission reaction rate over the active fuel height, with lateral bounds of ±7.5 assembly pitches so each mesh bin aligns to one assembly pitch, extracts the tally bins corresponding to those 58 detector positions, and normalizes the calculated values and measured values separately to mean 1. It then reports:

- normalized-map RMSE and MAE;
- mean absolute relative error;
- Pearson correlation;
- k_eff and its Monte Carlo standard deviation;
- per-detector raw tally standard deviation and relative Monte Carlo statistical uncertainty (before normalization);
- per-assembly measured/calculated values and residuals;
- statepoint SHA-256 and run settings.

This is a shape comparison of normalized detector measurements and calculated assembly fission rates. It is not absolute-power validation. The benchmark's detector signal and the model's volume-integrated fission-rate tally are related observables but not identical measurement operators; the result must be interpreted as a first comparison, not an exact detector-response calculation. Normalization-induced covariance between bins and experimental measurement uncertainty are not propagated by the runner.

## Pre-run source-mapping audit

A source-level audit against the pinned upstream `Core.core_lattice_template` mapped all **58/58** nonblank raw detector labels to unique assembly positions inside the declared 15×15 mesh. A second source-level check found all **58/58** labels in the 176-position tilt-corrected map; only those measured detector positions are used for comparison. The runner unit tests cover one-based mesh indexing, reversed lattice/mesh y orientation, duplicate labels, and normalization. This confirms label coverage only; it does not replace a coordinate-level audit of the generated OpenMC geometry and statepoint mesh.

## State-matching assumptions that require review

The Cycle 1 day-0 summary reports average boron 975.25 ppm, inlet coolant temperature 558.875°F (565.858 K), and control-bank withdrawals A/B/C/D/SE = 228/228/228/213/230 steps. The upstream builder default uses nominal 975 ppm, temperature 566.483 K (about 0.625 K higher), and SE at 228 steps. The runner overrides SE to 230 to match the recorded state while retaining the upstream axial step width. Because this exceeds the generic helper's 228-step input guard, it is an explicit adaptation that requires geometry and sensitivity review; it is not automatically validated merely because OpenMC runs.

Prior BEAVRS radial-map uncertainty work reports 95% confidence values of about 1.4% from theoretical analysis and 1.8% from repeated radial measurements; these are global benchmark-level estimates, not per-detector uncertainties in the CSV ([Liang et al., Quantifying Uncertainty in the BEAVRS Benchmark](https://www.researchgate.net/publication/326261983_Quantifying_Uncertainty_in_the_BEAVRS_Benchmark)). The later BEAVRS uncertainty paper treats tilt-correction uncertainty and reports 95% time-dependent uncertainty values of 1.8% for Cycle 1 and 1.9% for Cycle 2 ([Kumar et al. 2020](https://doi.org/10.1016/j.pnucene.2020.103488)). The runner does not yet propagate per-position measurement uncertainty or normalization-induced covariance and does not model the detector response exactly. **Even a favorable numerical result is preliminary evidence, not a complete experimental-validation certificate.**

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



## Final corrected-run result — 11 October 2026

Run: [GitHub Actions 38117279412](https://github.com/thenextw4ng/cb-pfr/actions/runs/38117279412)  
Artifact: [beavrs-cycle1-map-comparison-38117279412.zip](https://github.com/thenextw4ng/cb-pfr/actions/runs/38117279412)

- OpenMC transport completed at 500 batches (50 inactive, 3,000 particles/batch).
- Criticality consistency: (k_\mathrm{eff}=1.00036455\pm0.00076289). The 95% Monte Carlo interval includes unity. This is a consistency check for the modeled critical state, not by itself a complete validation certificate.
- Spatial comparison against the tilt-corrected map at 58 instrumented positions: normalized RMSE **0.33426**, normalized MAE **0.27573**, mean absolute relative error **29.00%**, Pearson correlation **−0.0780**.
- Mean / maximum raw-bin relative Monte Carlo tally standard deviation: **2.45% / 3.75%**.
- Independent artifact-integrity audit: **PASS_INTEGRITY_ONLY**, zero failed integrity checks.

### Interpretation

The model reproduces the critical condition within its Monte Carlo uncertainty, but the spatial map comparison is poor and does **not** pass as a validated flux-shape comparison. Therefore the overall BEAVRS physical-validation gate remains **NOT ESTABLISHED**. The next technical task is to resolve the model-to-observable mismatch (the assembly-integrated fission-rate proxy is not the detector response operator), examine the fuel-loading and detector-position mapping independently, and propagate benchmark uncertainty before making a physical-validation claim.

The run manifest records SE=230, matching the Cycle 1 day-0 record. The archived comparison JSON's limitation list retained one stale sentence about the upstream SE=228 default; the manifest and source configuration show the actual override. The result's integrity audit checks artifact consistency, not scientific adequacy. A source fix was committed afterward, and a metadata-clean rerun is in progress at [workflow 38117736764](https://github.com/thenextw4ng/cb-pfr/actions/runs/38117736764); it does not change the physics configuration or the interpretation of the completed comparison.

## First-run correction record

The first completed OpenMC run exposed a mesh-extent error: 17 mesh bins were placed across only 16 assembly pitches. Its preliminary comparison returned k_eff = 0.998612 ± 0.001239, normalized-map RMSE 0.37981, and Pearson correlation −0.21228. These metrics are recorded for transparency, but that result is superseded and must not be used as validation evidence because the mesh did not align one-to-one with assembly pitch. The runner now uses ±8.5 assembly pitches, reports raw tally statistical uncertainty, and the workflow uses a higher default budget (500 batches, 50 inactive, 3,000 particles/batch) plus an independent artifact-integrity audit. The corrected runs are tracked at [the lower-budget mesh-correction run](https://github.com/thenextw4ng/cb-pfr/actions/runs/38116769919) and [the higher-budget run with independent audit](https://github.com/thenextw4ng/cb-pfr/actions/runs/38116778762). Their output must be reviewed before any experimental-comparison claim is made.


## Additional state-matching correction — 11 October 2026

Source inspection found that the upstream BEAVRS builder sets the default operating temperature to 566.483 K, while the Cycle 1 day-0 summary reports an inlet temperature of 558.875°F (565.8583 K). The runner now sets the model's OpenMC temperature default from that recorded value and stores both the selected temperature and upstream default in the manifest. This removes a known avoidable state mismatch, but does not resolve the poor spatial comparison by itself. The new code and conversion test have been committed; the resulting transport rerun and artifact review are required before judging whether the map discrepancy changes.

The previous run's result remains an observed result for its recorded configuration, not a pass. The corrected-temperature run is tracked through the [BEAVRS workflow](https://github.com/thenextw4ng/cb-pfr/actions/workflows/beavrs-cycle1-map-validation.yml). Even if the next run improves, a physically defensible detector-response operator, uncertainty treatment, and predeclared acceptance criteria are still needed.


## Observable-operator correction — U-235 fission tally

The BEAVRS specification describes the 58-position radial maps as derived from in-core U-235 fission-chamber signals, and the benchmark text recommends comparing measured data with an axial edit of a tally such as U-235 fission. The runner previously tallied total fission over all nuclides, which is a weaker proxy for a U-235 chamber-derived signal.

The runner has now been changed to score `U235` fission specifically in the assembly mesh, while retaining the active-fuel-height integration. This is a closer observable match, but still **not an exact detector-response model**: the calculation does not explicitly reproduce the chamber, the 61 axial detector positions, detector response/gain processing, or the full measurement-uncertainty covariance. A fresh transport run is needed; previous total-fission metrics must not be presented as results from the U-235 tally configuration.

Sources: BEAVRS v2.0.1 specification, Section 3.2 (radial map construction and U-235 fission tally guidance); BEAVRS measurement documentation and uncertainty analysis. See [BEAVRS repository](https://github.com/mit-crpg/BEAVRS), [benchmark specification PDF](https://bamboo.xjtu.edu.cn/images/48970167_beavrs_2.0.1_spec.pdf), and [BEAVRS uncertainty paper](https://doi.org/10.1016/j.pnucene.2020.103488).


## Coordinate-registration audit — 11 October 2026

The archived U-235 run was inspected beyond its aggregate metrics. The generated mesh is 15×15 with bounds ±7.5 assembly pitches, matching one assembly pitch per bin. The pinned OpenMC 0.15.3 RectLattice documentation states that universe arrays are top-down views and that increasing the array's y index corresponds to decreasing physical y. The current source-level map (template row 2 → mesh y-bin 15, template row 16 → mesh y-bin 1, and template column to mesh x-bin) is consistent with that documented array convention. This source-level consistency does **not** prove the measurement labels and physical axes have been registered to the same orientation.

A diagnostic of the archived tally grid evaluated the current mapping and alternative rotations/reflections without changing the submitted result. The current mapping reproduces Pearson correlation 0.0324. Some alternate coordinate transforms produce different correlations (the largest exploratory value was about 0.36), but none is accepted as a correction: choosing a transform because it improves the metric would be post-hoc tuning. This is evidence that coordinate registration deserves an independent check against the benchmark's detector-layout schematic and a plot/export of the actual generated OpenMC geometry before spending compute on another full transport run.

The next run should be gated on an independent, documented coordinate crosswalk from each detector label to (a) the BEAVRS assembly label, (b) the physical x-y assembly center in the generated geometry, and (c) the exact mesh bin. The crosswalk should be reviewed without looking at the resulting correlations, then tested with a synthetic asymmetric map whose expected orientation is known. Only after that audit should a new high-budget transport be launched. The current U-235 run remains NOT_ESTABLISHED for physical validation.

The earlier 17×17 / ±8.5-pitch wording in this report was stale and described a prior, superseded mesh configuration; the actual corrected runner and archived run use 15×15 / ±7.5 pitches.


### Coordinate crosswalk artifact

The runner now emits beavrs_coordinate_crosswalk.csv, listing the upstream template token, zero-based template row/column, one-based mesh x/y bin, calculated mesh-center coordinates in centimetres, and whether the assembly is one of the 58 instrumented positions. Its SHA-256 and row counts are recorded in the run manifest. This improves traceability and enables an independent review of the source-to-mesh mapping. It is explicitly marked SOURCE_DERIVED_CROSSWALK; GEOMETRY_PLOT_REVIEW_REQUIRED: because the table is derived from the same source template and mapping convention, it is not itself an independent proof of physical orientation. A geometry plot and benchmark detector-layout cross-check remain a precondition for another high-budget transport run.
