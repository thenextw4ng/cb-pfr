# Limitations and Scientific Guardrails

1. **Synthetic evidence is not physical evidence.** The reported feasibility rates come from a deliberately artificial response generator.
2. **Uncertainty multipliers are not automatically confidence intervals.** A 1.96 multiplier does not create a 95% guarantee without an appropriate statistical model and calibration.
3. **No physical validation is established.** The current QUBO labels cannot be defensibly mapped to the executed C5G7 benchmark.
4. **Normalization and weights matter.** Changing scales or weights can change the ranking.
5. **No universal superiority claim.** The observed synthetic advantage is conditional on the released data-generating process and protocol.
6. **No safety claim.** CB-PFR is not a reactor-safety method.
7. **Archival artifact gap.** The released runner and configuration can generate the synthetic benchmark, and CI checks the reproduction path. However, the original 4,000-row archival `per_seed_results.csv` is not yet checked into this public repository, so readers cannot compare every generated row against that original file from the repository alone.
8. **Physical mapping remains unresolved.** MC/DC C5G7 execution evidence is separate from CB-PFR physical validation. The mapping audit status remains `NO_DEFENSIBLE_MAPPING_FOUND`.
