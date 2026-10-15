# ICIMCIS 2026 manuscript revision audit

## Manuscript framing

**Title:** Confidence-Bounded Physical Feasibility Ranking for Neutronic Screening of QUBO-Feasible Fuel Layouts Using OpenMC

This is an anonymous exploratory research-software/case-study submission. It does not claim that CB-PFR is a validated engineering method, that a physical optimum has been identified, or that any quantum or classical optimizer has demonstrated superiority. All six layouts are enumerated, and no pre-physics optimizer or annealer was run.

## UMMU protocol audit: do not merge the run sets

Two archived three-seed UMMU run sets share the same 7,000 total batches, 10,000 particles per batch, one thread, unique seeds, the same MGXS SHA-256, the standard seven-group C5G7 energy boundaries, and passing raw-HDF5 audit checks. They differ in inactive batches and were generated in separate GitHub Actions runs.

- Protocol A, run 38196703024, used 500 inactive and 6,500 active batches. Mean k-effective = 1.1864932117951554; between-run sample SD = 1.556837187208877e-4 (15.57 pcm); pooled within-run reported SD = 9.578820503799072e-5 (9.58 pcm); absolute difference from the project scalar reference 1.18655 = -5.678820484456004 pcm; relative convention = -4.785993413219843 pcm.
- Protocol B, run 38103032861, used 100 inactive and 6,900 active batches. Mean k-effective = 1.186473575493143; between-run sample SD = 7.697816030244766e-6 (0.77 pcm); pooled within-run reported SD = 9.445829436284311e-5 (9.45 pcm); absolute difference from the same reference = -7.642450685696467 pcm; relative convention = -6.440900666382762 pcm.

The between-/within-run SD ratio is 1.625 for Protocol A and 0.0815 for Protocol B. Protocol B is markedly under-dispersed relative to its reported within-run standard deviations. Its three OpenMC logs each record repeated “Fission source site(s) outside of entropy box” warnings (7,000 records per run in the collected logs), and its first-to-last active-quartile source-entropy shifts are very large (-0.475 to -1.456). This is a diagnostic concern, not evidence of unusually reproducible physical results. Protocol A's k-generation first-to-last active-quartile changes are +42.1 to +65.1 pcm; Protocol B's are -16.1 to +23.5 pcm. These descriptive summaries do not certify source convergence.

The original aggregation job for Protocol A failed because a source-convergence diagnostic artifact was absent for seed 720000; the three OpenMC runs themselves had completed and their raw-HDF5 audits passed. Protocol B's aggregate job completed, but aggregate completion does not resolve the dispersion and entropy-mesh concerns. The manuscript reports both protocols separately, does not select either as a validated canonical estimate, and explicitly calls for further review.

## Combined-uncertainty score convention

The scalar reference is 1.18655. The configured reference standard uncertainty is 9.5e-5 in absolute k-effective units, equivalent to 9.5 pcm; it is not a relative uncertainty or an official C5G7 acceptance tolerance.

For a descriptive and conservative project-level comparison, the manuscript defines:
- within-run standard error of the mean: pooled within-run SD divided by sqrt(n);
- between-run standard error of the mean: sample SD of run means divided by sqrt(n);
- run-mean uncertainty used in the score: the larger of the previous two values;
- combined standard uncertainty: sqrt(reference uncertainty squared + run-mean uncertainty squared);
- z score: (mean k-effective - scalar reference) divided by combined standard uncertainty.

This gives Protocol A z = -0.4342 and Protocol B z = -0.6977. The scores are descriptive sensitivity quantities only; they are not calibrated confidence intervals, a benchmark-validation test, or a safety/engineering acceptance criterion. The analyzer script now records the two source uncertainty components and the between-/within-run SD ratio explicitly.

## Six-layout campaign and CB-PFR screen

- Main campaign: 18 recorded multigroup OpenMC runs, six layout labels, three seeds per label; 7,000 total batches, 500 inactive batches, 10,000 particles per batch, two threads. Records have unique statepoint hashes, a shared MGXS hash, and the documented C5G7 seven-group structure.
- Symmetry classes under p01 <-> p10: S1 = {MMUU, MUMU}; S2 = {MUUM}; S3 = {UMMU}; S4 = {UMUM, UUMM}.
- For the composition penalty E(y) = A(sum y_i - 2)^2, every exactly-two-MOX feasible assignment has QUBO energy zero. No pre-physics optimizer/annealer result is reported.
- The illustrative limits remain retrospective: k-effective in [1.14, 1.21], Fmax = 1.35, z = 1, scales d_k = 0.01 and d_F = 0.1, unit weights. The sweep remains exploratory. At these values, two symmetry classes (three labels) pass and two classes fail. This is not an engineering or safety decision.
- Independent review of model identity/geometry/material mapping and benchmark-compatible spatial-tally correspondence is still outstanding. No full C5G7 benchmark validation or source-convergence certification is claimed.

## Literature and editorial revisions

1. Changed the manuscript and PDF metadata title to the user-specified title above.
2. Added and cited reactor-loading-pattern optimization literature, including Chapot et al. (1999), Wu (2001), Erdoğan and Geçkinli (2003), Zameer et al. (2014), Sobolev et al. (2017), and Abuzlf and Gilad (2025).
3. Kept constraint-handling and simulation ranking-and-selection citations separate from NIST uncertainty guidance.
4. Removed internal workflow status strings and phrases such as “corrected-group,” “saved scalar reference,” “saved project screen,” and “high-compute.”
5. Retained explicit evidence limits: no physical optimum, no calibrated confidence coverage, no full benchmark validation, no comparative superiority, and no quantum advantage.

## Supplementary source files

- `canonical_high_budget_summary.csv` is now a six-row run-level UMMU table for both protocols. The package should expose it under the human-readable name `ummu_run_level_protocol_audit.csv`.
- `results/cbpfr_physical_feasibility_bridge_2026-10-12.csv` contains the six-layout campaign.
- Analysis and ranking scripts are included so readers can inspect the operational calculations. The run-level UMMU file records seeds, individual run means/SDs, trace summaries, MGXS/statepoint hashes, and the number of entropy-mesh warning messages per run.

## Submission conditions

- Rebuild PDF from current TeX/BibTeX and confirm no more than six pages.
- Confirm anonymous PDF metadata and body; keep author names/affiliations in EDAS metadata.
- Update the title in EDAS to the title above and upload the anonymous PDF under **Review manuscript**. Leave **Final manuscript** empty until camera-ready submission.
- This is not the camera-ready version. No repository DOI or permanent public release is claimed in the anonymous review package.


## Decision-support and formal-rule revision (2026-10-15)

- Reframed the information-systems contribution as an auditable decision-support component, without hiding the OpenMC/fuel-layout case study or claiming a reactor-design validation.
- Added four formal rule properties (monotone violation in \(z\), permutation-invariant substantive ranking/tie groups, fail-closed invalid data, and point-estimate reduction at \(z=0\)).
- Fixed the substantive rank key in \`src/cbpfr/ranking.py\`: input index is no longer part of the score; candidate identifier is only a deterministic display tie-breaker. Added unit tests in \`tests/test_cbpfr_properties.py\`.
- Added exploratory Welch intervals for the mirror-pair differences using three runs per label. Because no equivalence margin was prospectively registered before examining these runs, the intervals are descriptive and do not establish formal equivalence.
- Expanded the decision table to show \(V_k\), \(V_F\), \(V_{\mathrm{total}}\), and rank/tie group. \(V_k=0\) for all classes under the current illustrative setting; the screen is therefore \(F\)-driven in this case.
- Reworked the figure to show \(B_F^+\) for \(z=0,1,2\) and a zoomed, explicitly illustrative threshold-crossing panel. The zoom threshold is explanatory only; it is not used as an acceptance limit.
- Added Runarsson and Yao's stochastic-ranking reference, separately from Deb's feasibility-first rule and NIST uncertainty guidance.
- The manuscript build, unit-test outcome, and PDF anonymity scan must be rechecked after these edits before submission. The OpenMC entropy mesh has not been repaired or rerun in this revision, and no replication experiment has been run.
