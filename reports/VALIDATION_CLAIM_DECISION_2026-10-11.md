# Validation claim decision — 2026-10-11

## Decision

**Do not label CB-PFR as experimentally or physically validated.** The strongest claim supported by the current repository is that CB-PFR is an implemented uncertainty-aware post-optimization ranking method with a reproducible synthetic benchmark and passing automated software CI. The repository also contains exploratory OpenMC/C5G7 execution and evidence-integrity checks. These are not proof that CB-PFR improves physical reactor outcomes.

This is a decision on claim wording, not a declaration that the research project has failed.

## What was checked

1. The repository's KRITZ-2 evaluator, scripts/evaluate_kritz2_reference.py, compares a user-supplied k-effective estimate and standard deviation with published participant-solution means. It does not execute OpenMC, reconstruct the experimental core, or establish validation. Its output correctly remains NOT_ESTABLISHED.
2. The OECD/NEA KRITZ-2 benchmark concerns critical configurations made from regular lattices of either UO2 or MOX rods in light water, at room and elevated temperature. It does not include interspersed UO2/MOX configurations that would directly validate the project's six 2×2 C5G7 placement candidates.
3. A publicly available OpenMC model located during this review is explicitly an infinite-lattice reflective pin-cell model, not a finite experimental-core model. Its k-infinity result must not be compared as though it were the experimental finite-core k-effective. The model is useful as a lattice-physics exercise only.
4. The repository's C5G7 runs and HDF5 audits establish that selected simulations ran and that their artifacts pass specified integrity checks. They do not, by themselves, establish convergence-grade benchmark agreement, validated candidate ranking, or a defensible mapping from legacy fresh / once_burned / twice_burned QUBO labels to C5G7 materials.
5. The 1,000-trial synthetic benchmark is evidence about the method under its declared synthetic data-generating process only. It is not nuclear experimental evidence.

## Claim matrix

| Proposed statement | Decision | Reason |
|---|---|---|
| “CB-PFR is an implemented uncertainty-aware post-optimization ranking method.” | Supported | Code and tests are in the repository. |
| “The released 1,000-trial synthetic benchmark reports a selected latent-feasibility rate of 0.976 for CB-PFR under its specified protocol.” | Supported with scope caveat | Reproducible synthetic evidence; not a universal superiority claim. |
| “The software test suite passes on Python 3.10, 3.11, and 3.12.” | Supported for the recorded CI run | This is software CI, not physical validation. |
| “OpenMC/C5G7 execution and evidence-integrity audits have been performed.” | Supported with scope caveat | Some runs are smoke/exploratory and do not constitute benchmark-grade validation. |
| “CB-PFR is experimentally validated against KRITZ-2.” | **Not supported** | No matching, audited finite-core OpenMC calculation and acceptance analysis is recorded. |
| “CB-PFR physically improves nuclear-fuel loading optimization.” | **Not supported** | The QUBO-to-physical mapping, objective, and candidate-level validation are not established. |
| “The six 2×2 C5G7 layouts are validated by KRITZ-2.” | **Not supported** | They are different benchmark configurations; KRITZ-2 does not test the mixed UO2/MOX placement layouts. |

## Exact wording recommended for paper, profile, and presentation

> I developed CB-PFR, an uncertainty-aware post-optimization candidate-ranking method for QUBO-generated candidate pools. Its implementation is accompanied by automated tests and a reproducible 1,000-trial synthetic benchmark. OpenMC/C5G7 work is currently exploratory computational evidence; experimental nuclear-physics validation and a defensible mapping from the legacy QUBO state labels to physical fuel configurations remain unestablished.

Short version:

> **Method/software validated on its synthetic benchmark; nuclear-physics validation not yet established.**

Do not shorten this to “physically validated,” “validated against KRITZ-2,” or “proven to improve reactor loading.”

## What would actually close the physical-validation gate

A physical-validation claim can only be promoted after all of the following evidence is added:

1. A frozen, source-cited KRITZ-2 configuration and a model whose geometry, isotopics, temperatures, moderator density/boron, water level/leakage, and boundary treatment match that configuration.
2. A runnable OpenMC input and the exact nuclear-data library/version, plus recorded software versions, seeds, particle/batch/inactive settings, logs, and statepoint hashes.
3. A source-convergence and statistical-precision assessment, with independent seeds where practical.
4. A comparison against the correct benchmark observable, with residuals in pcm and a defensible treatment of calculation and reference uncertainty. Participant-to-participant spread must not be relabeled as experimental measurement uncertainty.
5. A predeclared acceptance criterion and independent audit of the input-to-result chain.
6. Separately, a defensible QUBO-to-physical configuration mapping and candidate-level experiment/benchmark protocol before claiming CB-PFR physical effectiveness.

Passing KRITZ-2 alone would validate only the matched KRITZ-2 model path. It would not validate the unrelated C5G7 layout study or prove CB-PFR improves reactor optimization.

## Sources

- OECD Nuclear Energy Agency, *Benchmark on the KRITZ-2 LEU and MOX Critical Experiments — Final Report*, NEA/NSC/DOC(2005)24: https://oecd-nea.org/jcms/pl_18320/benchmark-on-the-kritz-2-leu-and-mox-critical-experiments-final-report
- Official report PDF: https://www.oecd-nea.org/upload/docs/application/pdf/2019-12/nsc-doc2005-24.pdf
- Public OpenMC KRITZ-2 model inspected: https://github.com/jtramm/input_examples_openmc/blob/4e9d1a45375c07103deddf3f408c6ebcc2395bb7/fission/kritz2/model.py (the model identifies itself as an infinite-lattice pin-cell model).
- Project comparison utility: scripts/evaluate_kritz2_reference.py
- Project benchmark gate: config/benchmarks/dual_benchmark_validation_manifest.json

## Final status

**Claim wording repaired; physical validation remains NOT ESTABLISHED.** No simulated value has been fabricated, no illustrative evaluator input is treated as a result, and no smoke run is promoted to experimental validation.
