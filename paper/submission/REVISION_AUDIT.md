# ICIMCIS 2026 manuscript revision audit

## Manuscript framing
This version is an anonymous, exploratory research-software/case-study submission. Its title does not imply that the study has demonstrated a unique physical ranking or a scalable optimizer benefit.

## Primary results used
- Main corrected-group campaign: 18 OpenMC runs, six layout labels, three runs per label, 7,000 batches, 500 inactive batches, 10,000 particles per batch, two threads; common MGXS hash and unique statepoint hashes.
- Canonical high-compute screen from workflow run 38103032861: three independent UMMU runs, seeds 720000/730000/740000, 7,000 batches, 100 inactive batches, 10,000 particles per batch. Mean k-effective 1.186473575493143; between-run sample SD 7.697816030244766e-06; pooled within-run reported SD 9.445829436284311e-05; maximum individual-run SD 9.480675330943125 pcm; absolute delta -7.642450685696467 pcm; reported project-screen z=-0.8035896053516894.
- Project-screen z is conditional on the saved code's reference standard uncertainty 9.5e-5 in absolute k-effective units; it is not treated as benchmark validation.
- Source artifacts and raw HDF5 audit passed their scripted checks; the workflow status explicitly says full benchmark remains blocked. No independent signed model/tally fidelity sign-off is available.
- Main six-layout per-class quantities were recomputed from results/cbpfr_physical_feasibility_bridge_2026-10-12.csv in the repository. QUBO energy is zero for every exactly-two-MOX feasible assignment.
- Reflection pairs under p01 <-> p10: S1 = {MMUU,MUMU}; S2 = {MUUM}; S3 = {UMMU}; S4 = {UMUM,UUMM}.

## Main revisions
1. Title reframed as an exploratory CB-PFR screening study.
2. Explicitly states no pre-physics optimizer/annealer was run and the composition-only QUBO is degenerate.
3. Removes the selector's MMUU label as a unique selected physical layout; reports mirror class ties.
4. Adds k bounds and normalized violation status for each symmetry class.
5. Replaces the connected threshold plot with a categorical sensitivity table reporting label and class counts.
6. Fixes figure caption: the chart shows means only; dispersion is tabulated, not claimed as plotted error bars.
7. Removes “missing from earlier paper draft”, “review-required”, and other internal-audit wording.
8. Uses the primary OECD/NEA C5G7 report; the Song et al. study is cited only as a related deterministic transport method, not as a primary benchmark reference.
9. Reports the canonical high-compute UMMU statistics from workflow run 38103032861, not the prior inconsistent mean.
10. Distinguishes absolute pcm (-7.64) from relative pcm (-6.44) conventions.
11. Drops the normalized-distribution comparison table because dependent normalized fractions were not supported by a formal covariance-aware validation analysis.
12. Keeps claims evidence-bounded: no full physical validation, convergence certificate, physical optimum, comparative superiority, or quantum advantage.

## Remaining submission conditions
- PDF build must pass in GitHub Actions and be confirmed at no more than six pages.
- Reviewer PDF remains anonymous; keep author names/affiliations in EDAS metadata, not in the review PDF.
- Update the EDAS paper title to match this manuscript title before submitting.
- This is not the camera-ready version. No repository DOI or release is claimed.
