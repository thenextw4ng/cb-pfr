# Corrected-group C5G7 evidence audit and remaining scientific gates

This report audits the committed 18-run corrected-group smoke study at
`results/c5g7_corrected_group_repeatability_smoke_2026-10-11/run_level_fission_objective.csv`.

Reproduce the evidence-integrity audit:

```bash
python scripts/audit_c5g7_corrected_objective.py \
  --runs-csv results/c5g7_corrected_group_repeatability_smoke_2026-10-11/run_level_fission_objective.csv \
  --out /tmp/c5g7-corrected-objective-audit.json
```

The audit checks six expected layouts, three runs per layout, unique seeds and
statepoint hashes, one common MGXS hash, and standard-group audits. It computes
descriptive Student-t intervals for mean k_eff and the relative fission-peaking
proxy. With only three independent runs, these intervals are wide and
exploratory; they are not a convergence certificate.

## Current outcomes

- The corrected-group smoke study has 18 run records and six layouts.
- The reported fission objective is a dimensionless shape proxy
  `max(R_a)/mean(R_a)`, where `R_a` is the integrated mesh fission tally
  assigned to each of four fuel assemblies. It is not absolute power.
- The MUMU layout has the lowest descriptive fission-peaking mean in this
  smoke sample, but its mean k_eff is far below the canonical reference region.
  Therefore it must not be selected as a recommended design.
- No design-specific acceptable k_eff band has been provided or scientifically
  approved. The selection QUBO correctly remains blocked rather than inventing
  a band or emitting a false optimum.
- The legacy three-state burnup QUBO remains unmapped to UO2/MOX because
  burnup, irradiation history, isotopic compositions, depletion chain, and
  material provenance are not supplied. The mapping audit remains fail-closed.

## Remaining gates

1. **Benchmark-grade convergence:** run the canonical UMMU case at a higher
   common budget with independent seeds; check the k_eff and spatial response
   against the primary benchmark specification. The repository has a
   manually-dispatchable workflow in
   `.github/workflows/c5g7-canonical-convergence.yml`; the current 100-batch
   study is not a substitute.
2. **Physical mapping:** do not convert fresh/once-burned/twice-burned labels
   into UO2/MOX. This requires traceable depletion/material compositions and
   an independent domain review.
3. **Design objective:** approve a design-specific k_eff acceptance band,
   confirm mesh-to-assembly tally integration and uncertainty propagation, and
   predeclare ranking rules before a final selection study. No band is
   silently assumed by the code.

Passing this audit means only that the corrected smoke-study records are
internally consistent. It does not certify the benchmark, select a physical
winner, or establish reactor safety.
