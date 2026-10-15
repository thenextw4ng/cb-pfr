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


## Revision pass after the 2026-10-15 audit

- The framing is explicitly decision-support / auditable workflow. Deb-style feasibility-first and Runarsson–Yao stochastic ranking are cited as prior methods, not as claims of novelty or comparative superiority.
- The manuscript now states four formal software properties with corresponding unit tests: violation monotonicity with the common uncertainty multiplier; candidate permutation invariance and substantive tie preservation; fail-closed handling of missing/non-finite required inputs (even at zero metric weight); and the zero-multiplier point-estimate limit.
- The ranking implementation no longer uses input index as a score component. Rank and tie-group are assigned from substantive scores; candidate IDs order only the display records. Infeasible candidates with equal declared violation remain tied instead of being sorted by QUBO energy.
- The illustrative decision table now includes lower/upper $k$ bounds, $F$ upper bound, $V_k$, $V_F$, total violation, rank/tie-group, and status. In the $F_{\max}=1.35$, $z=1$ screen, $V_k=0$ for every class; therefore the split is driven by $F$ and the paper says so explicitly.
- Mirror-label differences are reported with independent-run Welch intervals in mirror_pair_comparison.csv. No equivalence margin was declared before data acquisition; the analysis intentionally makes no equivalence conclusion. The unit test checks only software properties; it does not test physical mirror symmetry.
- Figure 1 now plots class means and operational upper bounds at $z=0,1,2$ and includes a zoom near $F_{\max}=1.87$. Both cutoffs remain retrospective sensitivity settings, not engineering thresholds.
- The scalar C5G7 reference $k_{\mathrm{ref}}=1.18655$ and 9.5-pcm standard uncertainty are attributed to the NEA benchmark context and the cited reference study. They are not treated as validation of this model.
- Double-blind checks must be rerun on the rebuilt PDF and the entire assembled ZIP. The paper must remain at or below six pages; metadata author must remain blank; the package must not expose absolute paths, personal names, internal repository paths, or a claim of DOI/permanent release.

## Open B-level items (not silently marked complete)

- Protocol B still has 7,000 entropy-mesh warnings per run and an implausibly low between-run/within-run SD ratio. Re-running after correcting and auditing mesh bounds is a distinct OpenMC job, not covered by the TeX or unit-test build.
- Protocol A's $k$-generation trace shifts still require a prospective convergence criterion and re-evaluation.
- The replication experiment (R0/R1/R2/R3 methods over declared distances to threshold, Wilson intervals, coverage and rank/tie metrics) remains separate confirmatory work; it cannot be substituted by synthetic-only unit tests.
- No optimization-benefit claim is permitted without running a real pre-physics optimizer on an informative objective. This ICIMCIS revision retains the explicit nonclaim.


## Additional execution pass (2026-10-15)

- Added `EXPERIMENT_PREREGISTRATION_REPLICATION.md` before any follow-up simulation. It freezes the reference interpretation, source-readiness gate, replicate design, comparison rules R0-R3, boundary-distance scenarios, outcomes, and stop conditions. It explicitly states that no new runs have been executed.
- Added the minimal QUBO and ranking source modules to the anonymous supplement so the included formal-property test can be executed from the package without importing unrelated project subsystems.
- Reproduced the mirror-label Welch interval CSV from the archived 18-run table; the generated output matched the packaged CSV exactly. The output still does not establish equivalence because no margin was prespecified.
- Reproduced the exploratory symmetry screen: three label strings across two symmetry classes pass at the retrospective settings; all k bounds are inactive and F drives the split.
- The current artifact-builder environment does not have OpenMC installed, and corrected model inputs/raw statepoints are not present in the anonymous supplement. Therefore the entropy-mesh correction, reruns, and scored replication experiment were not executed here. They remain blocked on an OpenMC-capable environment with the original model/statepoint artifacts.
- The four formal-property tests were initially not runnable from the assembled supplement because the imported `cbpfr` package source was absent. The QUBO and ranking modules have now been bundled under `supplementary/cbpfr/`; re-run the test suite with `PYTHONPATH=supplementary python -m unittest discover -s supplementary/tests -v` in the assembled package and record its actual result before claiming the tests passed.
