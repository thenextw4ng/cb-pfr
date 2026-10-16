# ICIMCIS 2026 Stage 5 Manuscript Preflight Audit

**Audit date:** 2026-10-15  
**Scope:** IEEE conference review manuscript and supporting evidence excerpts  
**Status:** Conditional pre-submission pass; EDAS-specific settings still require author confirmation.

## Method contribution and claim boundary

The review manuscript now explicitly states that CB-PFR is a method proposed and implemented in this work. Its described algorithmic procedure combines structural-feasibility checks, user-declared physical-metric limits, operational uncertainty bounds, normalized violation scoring, and deterministic lexicographic ranking. The manuscript does not claim that CB-PFR is the first such method, that each individual component is unprecedented, that it outperforms a fair baseline, that physical validation is complete, or that quantum advantage has been demonstrated.

The composition-only QUBO result remains narrowly framed: it enforces exactly two MOX assignments among four variable fuel positions, and all six feasible layouts receive zero energy. This limitation applies to the specified objective, not to QUBO in general.

## Source and evidence checks

- The repository's methodological manuscript was updated on branch `research/cbpfr-four-gate-closeout-2026-10-12` to use explicit proposed-method attribution.
- The 18-row six-layout export was inspected. It contains six layouts with three records each, 18 distinct seeds and statepoint hashes, common recorded MGXS provenance, and the documented 7,000-batch / 500-inactive / 10,000-particles-per-batch settings. Table means and sample deviations in the conference draft match the archived objective audit at the displayed precision.
- The separate canonical UMMU archive was summarized independently across three seeds. The mean (k_{\mathrm{eff}}) is 1.1864932118, the between-seed sample standard deviation is 0.000155684, the pooled RMS within-run standard deviation is 0.000095788, and the maximum individual-run standard deviation is 0.000096983. Relative to 1.18655, the difference is -5.679 pcm. Combining the between-seed standard error with the stated 9.5-pcm reference uncertainty gives (z\approx-0.434).
- The four normalized assembly-distribution relative differences were recomputed from the three archived canonical assembly-fission records and the published reference assembly powers. They match the manuscript values of approximately +0.0530%, +0.0344%, -0.0395%, and -0.1790%.
- These checks establish consistency of the reported arithmetic with the archived records. They do not independently certify model fidelity, source convergence, benchmark validation for every altered layout, absolute power, or reactor safety.

## PDF and anonymity preflight

- Compiled with the IEEEtran conference class on A4 paper.
- Final review PDF: five pages, within the six-page limit stated in the published ICIMCIS author-guidelines page.
- PDF metadata author field is empty and the author block reads “Anonymous Authors.”
- Fonts are embedded; citations and bibliography resolved in the final build; page renders were inspected with no detected clipped equations or tables.
- The review PDF does not reveal the repository URL, author names, or affiliation in its body text.

## Venue-specific checks

The official ICIMCIS 2026 homepage lists full-paper submission through **18 October 2026**. The author-guidelines page specifies English, A4 paper, a maximum of six pages including references, IEEE conference format, double-blind review, and submission through EDAS.

Official pages:
- https://2026.icimcis.org/
- https://2026.icimcis.org/author-guideline/

The author-guidelines page contains a legacy sentence referring to “ICIMCIS 2020,” while the current homepage lists ICIMCIS 2026 dates. The conference's EDAS page was not accessible to this automated audit without its normal login/session. Therefore the author must confirm the currently configured track/category, upload requirements, any additional PDF checks, and deadline in the live EDAS account before submission.

## Remaining external actions

1. Log in to the official EDAS submission system and confirm the active ICIMCIS 2026 entry, paper category/track, page/anonymity requirements, and upload status.
2. Keep the submitted PDF anonymized. Enter the genuine author list and affiliations in the venue's author-registration fields, and only add them to the camera-ready manuscript when instructed.
3. Before upload, compare the exact PDF being uploaded with this checked five-page A4 review copy.
4. Do not describe this preflight as a successful submission, full physical validation, or a completed archival software release. No EDAS upload, PDF-eXpress transaction, DOI minting, or release tagging is recorded by this audit.

## Decision

**The manuscript passes the local Stage 5 source, arithmetic cross-check, anonymity, PDF geometry, bibliography, and rendered-layout preflight. Submission remains conditional on confirming the live EDAS configuration.**