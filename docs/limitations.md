# Limitations and Scientific Guardrails

1. **Synthetic evidence is not physical evidence.** The reported feasibility rates come from a deliberately artificial response generator.
2. **Uncertainty multipliers are not automatically confidence intervals.** A 1.96 multiplier does not create a 95% guarantee without an appropriate statistical model and calibration.
3. **No physical validation is established.** The current QUBO labels cannot be defensibly mapped to the executed C5G7 benchmark.
4. **Normalization and weights matter.** Changing scales or weights can change the ranking.
5. **No universal superiority claim.** The observed synthetic advantage is conditional on the released data-generating process and protocol.
6. **No safety claim.** CB-PFR is not a reactor-safety method.
7. **Archival results are now included.** `results/per_seed_results.csv` contains 4,000 method/trial rows for the recorded 1,000-trial synthetic study. Availability of this artifact supports inspection and row-level auditing; it does not by itself prove that a fresh run is identical or independently validated.
8. **Physical mapping remains unresolved.** MC/DC C5G7 execution evidence is separate from CB-PFR physical validation. The mapping audit status remains `NO_DEFENSIBLE_MAPPING_FOUND`.
9. **Statistical interpretation requires care.** Reported rates and paired comparisons are conditional on the synthetic generator, trial protocol, and comparison definition. They should not be generalized to reactor performance or other domains without new evidence.
10. **Working-paper status.** The PDF is a methodological working paper; it should not be represented as peer-reviewed or physically validated unless that status changes and evidence is available.
