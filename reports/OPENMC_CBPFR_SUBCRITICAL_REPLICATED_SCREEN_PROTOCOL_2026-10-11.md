# OpenMC CB-PFR replicated subcriticality screen

**Status:** exploratory computational screen only; not physical validation or safety certification.

## Purpose
Correct the direction of the subcriticality rule and compare policies on the same candidate pool using held-out seed runs. The prior screen used a lower-bound rule that was inconsistent with a subcriticality criterion.

## Candidates
Five distinct arrangements in the bundled OpenMC C5G7-derived 2×2 multigroup lattice: four fuel positions, three fuel positions, two adjacent fuel positions, two diagonal fuel positions, and one fuel position. Fuel/moderator universe placement is altered; this is a toy model and is not claimed to be the canonical C5G7 benchmark.

## Compute budget
Five independent seeds per configuration; 20 batches, 6 inactive batches, 500 particles per batch, two threads. Total: 25 OpenMC runs. This is intentionally inexpensive and may be noisy.

## Criterion
For a subcriticality screen, use an upper rather than lower uncertainty bound:
\[
\hat{k}_{eff}+z s \le 1.0.
\]
Here (s) is the sample standard deviation across the small set of seed replicates. This is an operational conservative screen, **not** a calibrated confidence interval. The threshold 1.0 is illustrative and not a licensing or safety acceptance criterion.

## Comparison
Leave-one-seed-out folds compare:
- point estimate: use mean (k_{eff}) as the screening value;
- CB-PFR-style: mean (k_{eff}+1.96\times) between-seed SD;
- uniform margin: mean (k_{eff}+0.02).

All policies use the same training candidates and the same held-out seed fold. The held-out outcome is whether the selected configuration's simulated (k_{eff}<1.0). The number of folds is only five and the candidate set is deliberately small, so the estimate is exploratory and cannot establish general superiority.

No QUBO-only policy is included: the repository does not yet contain a defensible mapping from QUBO variables/energy to these physical configurations. Inventing one would make the comparison misleading.

## Interpretation boundaries
Successful execution establishes that the code ran OpenMC on multiple distinct configurations and computed a held-out ranking comparison. It does not establish canonical C5G7 benchmark agreement, reactor safety, model validation, a valid QUBO-to-physics mapping, or general CB-PFR effectiveness. Those require validated geometry/materials/observable, benchmark comparisons, converged statistics, and predeclared acceptance criteria.
