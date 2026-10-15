# CB-PFR ranking replication preregistration
**Protocol version:** 1.0  
**Prepared:** 2026-10-15  
**Status:** registered; experiment not yet run  
**Scope:** software-behavior/repeatability study only, not physical validation or benchmark qualification.

## Questions
1. Does per-candidate uncertainty screening alter acceptance decisions in the intended direction near a declared threshold?
2. Does a candidate-specific uncertainty width outperform one shared fixed margin when short-run dispersion is heteroskedastic?
3. How often do point-estimate, fixed-margin, and confidence-bound rules disagree with a designated higher-budget *reference decision*?
4. Are substantive ranks and ties stable to input permutation and to the declared symmetry mapping?

## Analysis population and candidate handling
Use the four declared diagonal-reflection class representatives MMUU, MUUM, UMMU, and UMUM for the first-stage short-run campaign. This representative reduction is a mathematical symmetry assumption, not a statistically established equivalence of the recorded mirror-label observations. Retain the full six-label results for all descriptive checks and do not delete a label because its result is inconvenient. If a geometry/material mapping check invalidates the symmetry transformation, stop and run all six labels instead.

The existing 18-run/four-class campaign is the provisional higher-budget reference dataset for this exploratory calibration only. It is not known physical truth: the source-convergence and uncertainty-propagation questions remain open. Any error rate against it must be labelled **reference-disagreement rate**, not physical false-accept/false-reject rate.

## Run protocol
- Preserve the OpenMC version, pinned upstream commit, MGXS digest, standard seven-group energy boundaries, geometry, materials, tallies, and one-thread execution policy.
- Short budget: 500 total batches, 100 inactive batches, 3,000 particles per batch. Use distinct seeds per candidate and replicate, registered before launch.
- Replicate target: **R = 200 runs per representative candidate** at the short budget. Run seeds must be unique; store the seed, statepoint SHA-256, settings hash, MGXS hash, audit output, and source-convergence traces for every replicate.
- A higher-budget follow-up is not automatically run for all 800 short cases. Existing 7,000-batch records remain the provisional reference; if a future budget-matched confirmation is performed, register it as a protocol amendment before generating its results.
- Run operational checks at the first completed seed only: model builds, statepoint parses, mesh warnings, audit completeness, and runtime. These checks may stop a broken run; they must not be used to select favorable response outcomes or tune thresholds.
- Do not count a failed/invalid run as a pass. Preserve it and report the predeclared reason. A repeated run replaces it only if a deterministic predeclared technical failure reason is recorded; retain both the failed record and replacement provenance.

## Decision-rule comparisons
Evaluate all methods on the identical per-replicate candidate observations and budget:
- **R0:** point estimate / feasibility-first baseline (\z=0);
- **R1:** one shared fixed margin, with its numeric value declared before analysis;
- **R2:** candidate-specific operational bound at \z=1;
- **R3:** candidate-specific operational bound at \z=2.

For every comparison, the score/tie key is the substantive ranking score. Candidate ID is for deterministic display only and must not split ties. The evaluation must preserve the whole top tie group; it may not quietly convert the first sorted identifier into a unique winner.

## Threshold-distance design
Use the higher-budget reference (F_{ref,i}) and the short-run dispersion (s_{F,i}) to define exploratory per-candidate limits by (F_{max,i}=F_{ref,i}+d,s_{F,i}). The primary positive distances are (d\in\{0.5,1,2,4\}), matching the proposed near-threshold grid. Add the reflected negative distances (d\in\{-4,-2,-1,-0.5\}) so the design samples both sides of a reference boundary and can estimate both reference-disagreement directions. These candidate-specific thresholds are a calibration device only, not engineering limits and not a claim that the candidates share a common acceptance threshold.

Also report a common-threshold sensitivity analysis separately. Do not select its value because it favors CB-PFR; show the full declared sweep.

## Primary outcomes
For each method and distance cell, report:
- top-tie-group reference-feasibility fraction (expected feasibility under uniform selection from the unresolved tied set);
- reference-disagreement rates in both directions, explicitly not labelled physical error rates;
- decision agreement and per-candidate pass-set membership;
- empirical coverage of the declared operational bounds against the provisional reference, called *descriptive coverage* rather than calibrated confidence coverage;
- symmetry/tie-group preservation;
- top-(K) overlap and Kendall τ-b with ties handled explicitly (report tie-aware concordance separately from any scalar tie-breaker result).

Report Wilson intervals for binary proportions; for fractional top-tie outcomes use a prespecified cluster bootstrap resampling **replicate seeds** (10,000 bootstrap resamples, fixed bootstrap seed 20261015) and report percentile 95% intervals. Do not treat tied candidates within one replicate as independent replicates.

## Heteroskedasticity and uncertainty meaning
Report the short-run standard deviations per candidate, their ratio max/min, and the fixed-margin versus candidate-specific-bound comparison. (F=\max(R_a)/\overline{R}) is a nonlinear maximum of noisy tallies; the short-run SD of run-level (F) is not interchangeable with OpenMC's binwise standard error. Preserve run-level (F) values and document that correlated tally bins are not separately propagated unless a validated covariance procedure is added.

## Analysis and reporting safeguards
- Save the exact protocol file, code commit SHA, config hashes, run seeds, outputs, and statepoint checksums.
- Do not overwrite output directories or archived results.
- Keep all limits, seed allocation, exclusions, summaries, and metrics as defined above. Any deviation is a protocol amendment with timestamp and commit before reading the affected outcome values.
- Report unconditionally; do not infer universal CB-PFR superiority from one threshold-distance grid.
- This experiment does not establish a QUBO optimizer advantage, quantum advantage, a physical optimum, reactor safety, source convergence, or full C5G7 benchmark validation.
- **Execution status remains NOT RUN** until the prescribed replicates and analysis are complete. The separate three-seed entropy-mesh diagnostic rerun is not this replication experiment.
