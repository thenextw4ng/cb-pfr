# Limitations and Scientific Guardrails

1. **Synthetic evidence is not physical evidence.** The reported feasibility rates come from a deliberately artificial response generator.
2. **Uncertainty multipliers are not automatically confidence intervals.** A 1.96 multiplier does not create a 95% guarantee without an appropriate statistical model and calibration.
3. **No physical validation is established.** The current QUBO labels cannot be defensibly mapped to the executed C5G7 benchmark.
4. **Normalization and weights matter.** Changing scales or weights can change the ranking.
5. **No universal superiority claim.** The observed synthetic advantage is conditional on the released data-generating process and protocol.
6. **No safety claim.** CB-PFR is not a reactor-safety method.
7. **Archival results and rerun status.** `results/per_seed_results.csv` contains 4,000 method/trial rows for the recorded 1,000-trial synthetic study. The benchmark has also been independently re-executed from the released source and frozen configuration, with substantive trial-level fields and aggregate rates matching the archive exactly. This is not an external third-party replication.
8. **Physical mapping remains unresolved.** MC/DC C5G7 execution evidence is separate from CB-PFR physical validation. The mapping audit status remains `NO_DEFENSIBLE_MAPPING_FOUND`.
9. **Generator design may favor candidate-specific uncertainty.** In the released generator, standard error is tied to arrangement parity, which also shifts the latent response; the observation model is normal and the candidate-specific standard error is correctly calibrated by construction. Thus the uncertainty estimate is informative by construction, which may favor CB-PFR over controls that do not use candidate-specific uncertainty. Sensitivity to the predeclared uniform margin of 0.008 has not been reported and remains future work.
10. **Statistical interpretation requires care.** Reported rates and paired comparisons are conditional on the synthetic generator, trial protocol, and comparison definition. They should not be generalized to reactor performance or other domains without new evidence.
11. **Working-paper status.** The PDF is a methodological working paper; it should not be represented as peer-reviewed or physically validated unless that status changes and evidence is available.
