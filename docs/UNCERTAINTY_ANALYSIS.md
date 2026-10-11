# Uncertainty analysis

## Separate uncertainty sources

1. **Within-run Monte Carlo tally uncertainty:** OpenMC's reported standard deviation of a tally mean from batch statistics.
2. **Between-seed variability:** sample standard deviation and standard error across independent, identically configured runs with distinct seeds.
3. **Model and nuclear-data uncertainty:** not estimated by the current workflow.
4. **Reference uncertainty:** the uncertainty explicitly reported by the cited reference, kept separate from simulation uncertainty.

These sources must not be merged without a justified statistical model.

## Nonlinear assembly peaking factor

For each statepoint, the analysis first aggregates mesh means into each of four 17x17 fuel assembly regions, then computes

[
F_r=\frac{\max_a R_{a,r}}{\frac{1}{4}\sum_a R_{a,r}},
]

where (R_{a,r}) is the integrated fission tally for assembly (a) in independent run (r). The replicate script then estimates the sample mean, sample standard deviation, and standard error of the mean of (F_r) across distinct seeds. Because each (F_r) is calculated from a whole statepoint, this approach does not falsely treat bins within one mesh tally as independent observations.

The replicate aggregator validates a common candidate/layout, unique integer seeds, unique statepoint SHA-256 values, finite values, positive assembly rates, and at least two runs. In a real benchmark study, use at least three independent seeds for an initial screen and more runs if uncertainty or ranking remains inconclusive.

This estimator describes between-seed variability of the derived statistic. It does not isolate the intrinsic within-run Monte Carlo variance, and with few replicates it can be noisy. It also does not include model bias, nuclear-data uncertainty, or uncertainty in the benchmark reference.

## Ratio propagation

For (R=A/B), first-order propagation is

[
\operatorname{Var}(R)\approx\frac{\operatorname{Var}(A)}{B^2}
+\frac{A^2\operatorname{Var}(B)}{B^4}
-\frac{2A\operatorname{Cov}(A,B)}{B^3}.
]

The covariance term cannot be omitted by assumption when numerator and denominator derive from the same transport calculation. The current replicate approach avoids estimating this covariance from mesh bins: it computes each ratio per run and summarizes the ratio across independent seeds. It is an alternative estimator of between-run variability, not a claim that a full covariance matrix is known.

## Invalid data and reproducibility

Nonfinite values, negative uncertainty, nonpositive assembly rates, missing provenance, duplicate seeds, duplicate statepoint hashes, or mixed candidate identities must fail closed. The output is not overwritten; create a new output path for each analysis. Record code commit, OpenMC version, input hashes, statepoint hashes, and the complete seed list.


## Observed three-seed smoke results

Workflow [38112597526](https://github.com/thenextw4ng/cb-pfr/actions/runs/38112597526) produced 18 statepoints (six layouts × three independent seeds). For canonical UMMU, the per-run peaking values were 1.87393448, 1.91921140, and 1.86519360; mean (1.88611316), sample SD (0.02899519), and standard error (0.01674038). The three-run (k_{eff}) mean was (1.18610263), sample SD (0.00386340), standard error (0.00223053).

All six layouts have three seed replicates, but these are still smoke settings (100 batches, 10 inactive, 1,000 particles per batch). The between-seed standard error is descriptive; three replicates do not establish a calibrated confidence interval, and it does not include model/nuclear-data uncertainty.
