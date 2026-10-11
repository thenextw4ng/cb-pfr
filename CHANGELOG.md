# Changelog

## 2026-10-11 — Evidence audit and uncertainty/benchmark guardrails

- Added an implementation audit tied to the successful C5G7 quick-check commit and artifact.
- Added independent-statepoint aggregation for per-run assembly fission peaking metrics, requiring distinct seeds and statepoint hashes.
- Added a metric-aware comparison script for the single published C5G7 reference. It calculates the (k_{eff}) numerical difference but blocks comparison of maximum pin power with assembly-integrated fission-rate peaking.
- Recorded the low-statistics quick-check comparison and explicit validation limitations.
- Added model audit, execution, uncertainty, validation evidence, architecture, limitations, and reproducibility documentation.
- Preserved prior outputs and the original baseline CSV; no historical evidence was overwritten.


- Recorded successful 18-run corrected-group C5G7 repeatability smoke run (six layouts, three seeds each) with unique statepoint hashes and all group/spatial mapping audits passing; retained its compact provenance and uncertainty summary.
