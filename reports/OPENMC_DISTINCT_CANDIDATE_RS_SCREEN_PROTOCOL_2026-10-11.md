# Exploratory OpenMC screen: distinct physical configurations + R&S

**Status:** exploratory low-cost run; not a benchmark validation or safety analysis.

## Question
Can the OpenMC pipeline compare distinct physical configurations under equal simulation budgets and feed the observed estimates into a conservative ranking screen?

## Model and design
Uses OpenMC's bundled C5G7-derived 2×2 multigroup lattice example. Three configurations contain 3, 2, or 1 fuel pin universes with remaining positions filled by moderator-only universes. Each receives the same three independent seeds and equal settings: 12 batches, 4 inactive, 300 particles per batch. This is intentionally cheap and likely statistically noisy.

## Analysis
The script archives each run's (k_{eff}) estimate and OpenMC-reported standard deviation. It summarizes mean (k_{eff}), between-seed variability, and a CB-PFR-style lower-bound screen. It reports both ascending mean-(k_{eff}) ordering and conservative-screen ordering.

**Important:** (k_{eff}) alone is not a complete reactor-design objective; lower (k_{eff}) does not automatically mean a better or safe design. The threshold of 1.0 is a demonstration screen, not a validated acceptance criterion. This geometry manipulation is not claimed to preserve a canonical C5G7 benchmark.

## What a successful run supports
It supports that OpenMC executed multiple distinct geometry configurations at equal computational budgets, generated replicate estimates, and that a conservative ranking calculation can be applied to those estimates.

## What it cannot support
It cannot establish safety, design feasibility, canonical C5G7 benchmark agreement, a valid QUBO-to-physics mapping, or general CB-PFR/R&S superiority. Three seeds and very low histories are only a smoke/sensitivity screen. A confirmatory experiment needs a prespecified objective and acceptance criteria, more histories/replicates, independent held-out scoring, calibrated uncertainty, and benchmark verification.
