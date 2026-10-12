# CB-PFR C5G7 high-budget evidence review — 2026-10-12

Disposition: the three-seed canonical numerical screen passed its project-level scalar criteria. Physical validation remains blocked. This is a review of preserved statepoints, not an independent benchmark-specialist sign-off.

- Source high-budget workflow referenced by recovered artifact: 38196703024.
- Recovery workflow: https://github.com/thenextw4ng/cb-pfr/actions/runs/38222690312
- Recovery artifact ID: 11735016906.
- Artifact SHA-256: bc6f81587d5914b78bffebbb098e74e44e35bfcab6ebd3fa8a24731cbc064715.
- Upstream source commit: ba41bee54320ada0b4ac39a0dd2ca3c1d090a450.
- OpenMC 0.16.0; 7,000 batches, 500 inactive, 10,000 particles/batch, 1 thread, 3 seeds (720000, 730000, 740000).
- Total budget: 210 million nominal histories, 195 million active histories.
- All three raw HDF5 audits passed; unique seeds and statepoint hashes were recorded; the MGXS hash matched across runs.

## Scalar numerical screen

Mean k-effective = 1.1864932118; reference = 1.186550; difference = -5.6788 pcm; combined-uncertainty z = -0.4342; maximum individual-run reported standard deviation = 9.6983 pcm. The project numerical screen passed. This is not official benchmark acceptance.

## Source/eigenvalue diagnostics

Post-hoc exploratory OLS trend estimates with Newey–West/HAC standard errors (50 lags) were computed from the saved active-generation traces. The k-generation slope per 1,000 active batches and p-value were: seed 720000 +0.0001080 (p=0.294); seed 730000 +0.0000721 (p=0.518); seed 740000 -0.0000153 (p=0.894). Entropy slope per 1,000 active batches and p-value were: seed 720000 -0.0001411 (p=0.594); seed 730000 -0.0001563 (p=0.572); seed 740000 +0.0000819 (p=0.767).

These exploratory tests do not detect a statistically clear linear trend, but this is not proof of convergence. The tests are post hoc, can miss nonstationary or spatial source-mode behaviour, and are not predeclared acceptance criteria. The formal source-convergence status remains REVIEW REQUIRED.

## Spatial comparison limitation

The tally is integrated mesh `fission`, not absolute power in watts. The current comparison uses published assembly power values (492.8, 211.7, 211.7, 139.8) as a normalized spatial-shape reference. Observed normalized fission-rate fractions were p00 0.4669140, p01 0.2005424, p10 0.2003942, p11 0.1321494; normalized reference fractions were 0.4666667, 0.2004735, 0.2004735, 0.1323864. Relative differences were +0.0530%, +0.0344%, -0.0395%, and -0.1790%, respectively.

Exploratory combined-uncertainty z diagnostics were +0.584, +0.216, -0.240, and -0.817. These use a first-order delta-method propagation of published raw assembly-power uncertainties assuming independence because no covariance matrix was available, plus the standard error across only three run-level fractions. They are not official acceptance statistics and do not resolve whether fission-rate proxy and assembly power are fully comparable. This result should not be represented as full physical validation.

## Required closeout

1. Independent comparison of actual generated geometry, materials, cross sections, boundary conditions, tallies, and source treatment against the primary OECD/NEA C5G7 specification.
2. Qualified review of source/eigenvalue stationarity or a justified predeclared follow-up protocol.
3. Review of fission-rate-proxy versus power comparability and normalized uncertainty covariance.
4. Comparable transport evidence for all six layouts under a predeclared physical decision rule before claiming a physical winner.

Overall physical validation remains NOT YET PASSED. Do not run additional transport solely to obtain a preferred result; first document the unresolved question and acceptance rule.