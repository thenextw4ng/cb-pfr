# ICIMCIS manuscript audit — 2026-11-15

## Scope and source of truth

Audited the six-page uploaded manuscript CB-PFR_revised_manuscript_clean (1).pdf (uploaded 2026-11-15), against repository branches and available campaign artifacts. This note is an audit record, not a replacement manuscript. Do not build the uploaded PDF from the older LaTeX source found on paper/icimcis-high-compute-revision-2026-10-15: that branch contains an earlier C5G7/18-run paper version and is not source-equivalent to the current six-page manuscript.

## Executive disposition

| Work item | Finding | Required close-out |
|---|---|---|
| S1 OpenMC package | P1–P5 campaign records and P4/P5 audit material were recovered from Actions artifacts. Campaign inventory: 46 records (10 P1–P3; 36 P4–P5), 4,090,540,000 configured active histories. | Publish recovered files under a versioned supplement/S1_C5G7/ tree, include manifest and checksums, and link the exact archive in Data Availability. Do not describe all runs as converged: source diagnostics remain DIAGNOSTIC_REVIEW_REQUIRED. |
| S2 six-regime benchmark | Current PDF specifies 6 regimes × 1,000 pools, 12 candidates/pool, 200 development pools per regime, tuning grid 0–0.02 by 0.004, z=1, and 5,000 paired bootstrap resamples. Aggregate tables/protocol exist in the benchmark branch. | Publish per-pool and per-method records plus exact bootstrap/sign-test code and regenerated tables. Current Table II omits several interval endpoints despite the methods section claiming paired bootstrap intervals. |
| S3 independent S_N cross-check | Six-layout S_N output archives were recovered. Solver identity is pinned to EmreSakarya/c5g7-2d-transport-benchmark, commit db421c969ee2de83e2d2ae2b14bda368567b558d. | Publish six layout archives, source identity, settings, logs, normalized fields, and a clear note that terminal residuals were not retained and convergence is not certified. |
| S4 R1 synthetic benchmark | results/per_seed_results.csv on main contains 4,000 method-by-pool rows (1,000 pools × 4 methods); reported success rates match the manuscript: CB-PFR 97.6%, point estimate 93.3%, uniform margin 96.6%, QUBO-only 85.7%. | Include raw CSV, frozen protocol/configuration, exact paired-bootstrap and exact sign-test script, generated interval/sign-test tables, and checksums as S4. |
| LaTeX source | Available LaTeX/BibTeX on the older paper branch does not correspond to the 2026-11-15 PDF. | Reconstruct/export the actual final source package from the source used to produce this PDF; include all figures, bibliography, build instructions, and PDF checksum. |
| References | Current PDF has 36 numbered references. | Keep 36 if each is cited and verified; do not delete two solely to meet an old count. Correct Pasupathy/SCORE year: vol. 25, no. 1 is conventionally cited as 2015 (online-first 2014). Recheck each entry against DOI/publisher metadata and citation-key audit from final source. |

## Numerical evidence to preserve

### C5G7 / S1 and S3

- Six enumerated 2×2 fuel layouts: MMUU, MUMU, MUUM, UMMU, UMUM, UUMM.
- P1–P3: 10 records. P4/P5: 36 records (six layouts × three seeds in each campaign).
- P4 settings: 2,000 batches, 100 inactive, 5,000 particles/batch; P5: 20,000 batches, 500 inactive, 10,000 particles/batch.
- P5 means (assembly-integrated peaking proxy): MMUU 1.296065; MUMU 1.296538; MUUM 1.316332; UMMU 1.867369; UMUM 1.816200; UUMM 1.816087. MMUU–MUMU difference (~0.000473) is smaller than the larger of their reported between-seed SDs (0.000722); do not claim inferential separation.
- All methods selected MMUU in this six-layout screening cohort; this does not demonstrate a CB-PFR treatment effect or physical superiority.
- Independent S_N values are code-to-code diagnostics, not validation. Reported OpenMC–S_N differences are 148–223 pcm in magnitude and normalized-field RMS differences 7.53–7.91%; terminal residuals are absent.
- OpenMC source-convergence indicators remain DIAGNOSTIC_REVIEW_REQUIRED; quartile shifts are not a convergence certification.
- The peaking quantity is an assembly-integrated fission-rate proxy, not pin power, absolute power, a licensed metric, or a safety criterion.

### R1 / S4

- 4,000 rows = 1,000 paired pools × four methods.
- Success rates in the current PDF: CB-PFR 97.6%, point estimate 93.3%, uniform margin 96.6%, QUBO-only 85.7%.
- The PDF reports paired differences of +4.3 pp vs point [3.0, 5.7], +1.0 pp vs uniform [0.3, 1.7], and +11.9 pp vs QUBO-only [9.8, 14.0]. It reports discordant-pool sign tests 47 vs 4 (p < 10^-9) against point and 12 vs 2 (p = 0.013) against uniform.
- Recompute these from the archived 4,000 rows with a deterministic, documented resampling seed before submission; raw CSV alone is not a substitute for bootstrap/sign-test code.

## Manuscript corrections required before final PDF

1. Table II is incomplete. The methods section says 5,000-resample paired bootstrap intervals are used for S2, but Table II displays point differences without intervals for several low/moderate S2 comparisons and uses dashes for under-reported comparisons. Add the complete predeclared pairwise contrasts and 95% intervals, or explicitly label unavailable contrasts and remove claims implying all intervals are reported. Do not fill gaps with estimates from an older S2 dataset.
2. S2 count/regime labels must be identical everywhere. Section IV describes six regimes (three calibrated Gaussian, under-reported, contaminated, no-feasible). Ensure Table II, Results, Abstract, supplement, and Data Availability use the same names and include the no-feasible regime outcome. Current table lists low, moderate, high, under-reported, contaminated, but no-feasible is not shown.
3. T7 must remain explicitly exploratory. It is aggregate-only because per-pool outputs were not archived. Do not cite T7 as independently replicated or use it to support confirmatory claims.
4. R1/S4 artifact completeness. The PDF says the 4,000 rows and paired-bootstrap/sign-test scripts are archived. Ensure all exact artifacts are in S4 and Data Availability links resolve. main/results/per_seed_results.csv supplies the 4,000 rows, but package also needs scripts and output tables.
5. C5G7 claim boundary. Keep the statement that the cardinality penalty is equal across all six layouts and does not establish that QUBO generated them. Keep C5G7 separate from RQ1 synthetic effectiveness claims.
6. OpenMC/S_N convergence wording. Retain DIAGNOSTIC_REVIEW_REQUIRED, no convergence certification, and no physical-validation claim. S_N terminal residual absence must be disclosed in main text and S3 README.
7. References. Current PDF contains 36 entries. Preserve all references that are actually cited. Correct [4] to the 2015 issue year if citing vol. 25, no. 1 (online-first 2014 can be mentioned only if needed). Audit [1]–[36] against final LaTeX and confirm no uncited/uncatalogued entries.
8. Final source archive. The old branch's paper/submission/*.tex and references.bib are not source-equivalent to this PDF. Create a new source ZIP from the actual final manuscript, including main.tex, references.bib, figures, supplement references, README/build command, and SHA-256 hashes. Never silently substitute the older source.

## Recommended supplement tree

```text
supplement/
  S1_C5G7/
    README.md
    protocol_and_settings.md
    P123_run_summary.csv
    P45_seed_level_results.csv
    P45_run_inventory.csv
    P45_layout_summary.csv
    independent_transport_summary.csv
    openmc_sn_crosscheck.csv
    audit/
    manifest/
  S2_synthetic_six_regime/
    README.md
    protocol.json
    generator.py
    seeds.json
    development_pool_results.csv
    confirmatory_per_pool_results.csv
    paired_bootstrap.py
    paired_bootstrap_intervals.csv
    manifest.sha256
  S3_independent_SN/
    README.md
    solver_identity.txt
    settings/
    logs/
    six_layout_outputs/
    normalized_fields/
    manifest.sha256
  S4_R1_heterogeneous/
    README.md
    protocol.json
    per_seed_results.csv
    paired_bootstrap.py
    exact_sign_test.py
    paired_intervals.csv
    sign_test_results.csv
    manifest.sha256
source/
  manuscript_source_LaTeX.zip
```

## Submission gate

Do not call the package complete until (a) all supplement links are accessible without private GitHub credentials, (b) raw CSVs and scripts regenerate every displayed number, (c) final LaTeX source rebuilds the exact six-page PDF, (d) SHA-256 hashes are recorded, and (e) Data Availability lists exact S1–S4 filenames/URLs. No additional OpenMC run is required to close these documentation and reproducibility items.