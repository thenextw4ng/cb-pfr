# Low-cost OpenMC + CB-PFR/R&S smoke test

**Purpose:** establish a low-cost, reproducible integration gate for running OpenMC and exercising the CB-PFR-style ranking rule.

**Critical scope limitation:** this is not physical validation. The script uses OpenMC's Python API C5G7-derived multigroup 2x2 lattice example at low particle count. It then creates three *artificial perturbations of the same model's k-effective estimate*, not three independent reactor designs. The ranking step checks selection-rule plumbing and uncertainty-bound handling only. It cannot show CB-PFR improves physical design.

## Run
Workflow: `.github/workflows/openmc-cbpfr-low-cost-smoke.yml`. Intended budget: 20 batches, 5 inactive, 500 particles/batch, two threads. It installs OpenMC from conda-forge and uploads inputs and a JSON summary.

## Passing criteria
- OpenMC executable and Python API import successfully.
- Model completes to a statepoint and reports k-effective and its uncertainty.
- Summary captures settings and explicitly marks the physical status as `SMOKE_TEST_ONLY_NOT_ESTABLISHED`.

## Interpretation
A passing workflow establishes only that this small OpenMC example executes and ranking mechanics run. It is not benchmark-grade C5G7 validation and does not support reactor safety, design feasibility, CB-PFR effectiveness, or general R&S superiority. Physical-validation status remains `NOT_ESTABLISHED`.

## Actual physical comparison still required
1. Define distinct physical candidate configurations and a defensible QUBO-to-geometry/material mapping.
2. Freeze physical objective, feasibility threshold, convergence limits, and analysis plan before seeing results.
3. Use independent OpenMC seeds and equal particle-history budgets per candidate.
4. Use pilot runs to estimate candidate-specific uncertainty and held-out runs as truth.
5. Compare QUBO-only, point estimate, CB-PFR, and uniform-margin selection on identical pools.
6. Demonstrate convergence and agreement with a recognized benchmark before making physical-effectiveness claims.
