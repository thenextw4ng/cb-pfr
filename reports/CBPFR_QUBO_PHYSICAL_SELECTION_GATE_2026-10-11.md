# Stage 5 — CB-PFR/QUBO physical-selection gate

**Status: PIPELINE IMPLEMENTED; PHYSICAL VALIDATION NOT YET ESTABLISHED.**

This gate is designed to connect actual corrected-group OpenMC results to a conservative CB-PFR screen and a finite one-hot QUBO selector. It is deliberately fail-closed. It must not be described as completed physical validation until the input evidence, declared design criteria, and independent model review all pass.

## What this pipeline does

`scripts/run_c5g7_cbpfr_physical_selection.py` consumes a run-level CSV derived from corrected-group OpenMC statepoints. It requires:

- all six declared 2×2 UO₂/MOX layouts;
- at least three runs per layout, with distinct seeds within each layout;
- unique statepoint hashes and one common MGXS hash;
- the standard C5G7 seven-group boundaries and passing group-structure audits;
- one common compute profile across all runs;
- caller-declared minimum batch and particle budgets;
- an explicit design-specific (k_{eff}) interval, fission-peaking ceiling, uncertainty multiplier, normalization scales, and risk weight.

For each layout it calculates repeated-run means and sample standard deviations. The uncertainty envelope is explicitly an **operational heuristic**, not a calibrated confidence interval. The (k_{eff}) uncertainty used for the gate is the larger of the between-seed sample SD and mean reported within-run standard deviation; the fission-peaking uncertainty uses between-seed sample SD. The script never invents a feasible interval when no candidate passes.

For candidates that pass the declared conservative screen, it builds a one-hot QUBO over the six evaluated layout IDs. It exhaustively checks all 64 binary states and requires a unique one-hot minimizer. The selected ID must agree with the CB-PFR lexicographic choice (conservative feasibility/violation first, risk-adjusted fission-peaking score next). This verifies software consistency of the combined selector against the supplied physical-data table.

## Example invocation

The thresholds below are intentionally **not supplied**: they must be approved and recorded for the intended study before results are examined. Do not run the script with guessed limits.

```bash
python scripts/analyze_c5g7_fission_objective_repeatability.py \
  --study-root /path/to/corrected-group-study \
  --outdir /path/to/analysis

python scripts/run_c5g7_cbpfr_physical_selection.py \
  --run-level-csv /path/to/analysis/run_level_fission_objective.csv \
  --out /path/to/analysis/cbpfr_qubo_physical_selection.json \
  --keff-min <approved-lower-limit> \
  --keff-max <approved-upper-limit> \
  --fission-peaking-max <approved-upper-limit> \
  --uncertainty-multiplier <predeclared-value> \
  --keff-scale <approved-violation-scale> \
  --fission-peaking-scale <approved-violation-scale> \
  --risk-weight <predeclared-value> \
  --min-batches <approved-minimum-batches> \
  --min-particles <approved-minimum-particles>
```

The command's exit status only says whether the pipeline executed. Read its JSON `status`; `SELECTION_PIPELINE_PASS_PHYSICAL_VALIDATION_NOT_CERTIFIED` means the declared selector was consistent with its inputs, **not** that the reactor model has been certified.

## Required independent gates before publication

1. Review the exact model against the OECD/NEA C5G7 primary specification: geometry, boundary conditions, material compositions, nuclear data, seven-group boundaries, and tally definitions.
2. Review canonical-reference agreement using the corrected group structure and actual high-budget statepoints. Compare spatial fission/power quantities, not only (k_{eff}).
3. Approve the design-specific feasibility band and objective/normalization protocol before selecting among noncanonical layouts. The canonical benchmark scalar is not automatically an acceptance band for all six permutations.
4. Complete a common-budget repeated six-layout study, preserve raw statepoints/settings/logs/hashes, and review source convergence and tally uncertainty/covariance limitations.
5. Have an independent qualified reviewer inspect the mapping and protocol. A repository audit or green CI is not a substitute.
6. Keep the legacy `fresh / once_burned / twice_burned` QUBO separate. This C5G7 placement QUBO is a new, physically scored layout-selection formulation; it does not retroactively validate a depletion-state mapping.

## Current blocking evidence

- The corrected-group 18-run artifact is exploratory smoke-budget evidence (100 batches, 10 inactive, 1,000 particles per batch).
- The canonical high-budget run must complete and its statepoints/source-convergence diagnostics must be inspected.
- The intermediate six-layout run must complete with common settings and pass all raw-statepoint audits.
- No design-specific acceptance interval has been approved in the repository.
- The historical production MGXS used nonstandard group boundaries and is not valid benchmark-comparison evidence.
- No defensible physical mapping exists from the legacy burnup labels to C5G7 UO₂/MOX compositions.

## Permitted conclusion

After the pipeline passes on adequate, audited data, the strongest supported claim is that the **C5G7-specific layout QUBO and CB-PFR selection layer were exercised against corrected-group OpenMC simulation outputs under a declared screening protocol**. Official benchmark verification, reactor-safety benefit, and physical validation of the legacy burnup-state QUBO remain separate claims requiring their own evidence.
