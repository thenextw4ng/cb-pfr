# Eureka! ITB claim-to-evidence matrix — 11 October 2026

This document is a fail-closed checklist for the CB-PFR / ReactorQ Studio submission. A claim is allowed only when the corresponding evidence artifact exists and has been reviewed.

## Claim matrix

| Proposed claim | Minimum supporting evidence | Current disposition |
|---|---|---|
| “CB-PFR is an uncertainty-aware post-optimization ranking layer.” | Source code, method definition, tests, paper consistent with implementation | Supported as a methodological/software claim |
| “CB-PFR improves selection in the declared synthetic benchmark.” | Frozen configuration, trial-level records, prespecified comparison protocol, paired uncertainty analysis | Exploratory 1,000-pool benchmark showed a conditional synthetic effect. The 40,000-pool confirmatory test did **not** meet its prespecified ≥2 percentage-point practical-effect threshold (pooled gain +0.4875 pp); do not claim confirmatory synthetic superiority. Not physical evidence. |
| “The project uses QUBO.” | Explicit Q matrix/offset, candidate encoding, constraints, exact enumeration or solver output | Supported for the explicitly reformulated one-hot C5G7 layout-selection prototype |
| “The legacy fresh/once-burned/twice-burned QUBO models UO2/MOX physics.” | Defensible state-to-material/composition mapping and independently audited model generation | Not supported; no defensible mapping has been established |
| “The OpenMC model was compared against BEAVRS Cycle 1 day 0.” | Successful workflow run, pinned model/data provenance, statepoint, 58-bin comparison CSV, independent artifact audit | Supported as an executed comparison; integrity audit passed, but spatial agreement is poor (RMSE 0.33426, correlation −0.0780), so it is not validation evidence |
| “The model is physically validated.” | Matching experimental state, benchmark-specific uncertainty treatment, justified acceptance criteria, convergence and independent review | Not established. k_eff = 1.00036455 ± 0.00076289 is consistent with unity within Monte Carlo uncertainty, but the 58-position spatial map comparison is poor and detector-response/model-form uncertainty remains unresolved |
| “CB-PFR improves a physical reactor candidate ranking.” | Valid candidate-to-physics mapping, multiple physically evaluated candidates, repeated runs, common budget, uncertainty propagation, baseline comparison | Not established |
| “Quantum hardware was used.” | Archived actual annealer/quantum-device job, problem submitted, returned samples/results, device metadata | Not established by QUBO formulation or classical enumeration |
| “Quantum advantage was demonstrated.” | Fair comparison to suitable classical baselines over repeated trials and cost/time/quality metrics | Not established |
| “The author created and implemented CB-PFR.” | Authorship records, dated manuscript/repository history, clear separation of original contribution from standard QUBO/OpenMC components | Can be framed as authorship/development of the proposed CB-PFR method, subject to accurate disclosure |

## Six execution stages

1. **Baseline and reproducibility:** synthetic benchmark, implementation, test suite, source provenance, archival outputs. Mostly present; CI must remain green.
2. **Physics benchmark model:** selected BEAVRS upstream revision, OpenMC model generator, experimental Cycle 1 day-0 data, nuclear-data provenance. Model runner/workflow committed.
3. **Experimental comparison:** full-core OpenMC run, fission-map comparison, statepoint hashes, logs, residuals, uncertainty and acceptance-rule review. The 500-batch run and integrity audit completed; criticality consistency is promising, but spatial-map agreement is poor and the physical-validation gate remains open.
4. **QUBO-to-physics mapping:** keep the legacy burnup-state QUBO separate. The explicit 2×2 C5G7 UO2/MOX one-hot design is a separate reformulation and is not interchangeable with BEAVRS.
5. **CB-PFR physical effectiveness:** a software integration smoke now passes on 18 corrected-group C5G7 runs and the exact one-hot QUBO enumerates 64 states. This only checks pipeline consistency under illustrative limits; a defensible candidate space, justified physical constraints, benchmark-grade repeated evaluations, uncertainty propagation, and baseline comparisons are still needed.
6. **Release and claims audit:** preserve raw artifacts, document limitations, reproduce outputs from a clean checkout, and ensure every abstract/presentation claim maps to evidence. Final audit depends on stages 3–5.

## Quantum wording

QUBO is a binary quadratic optimization formulation. It can be solved by classical algorithms or submitted to quantum annealing/hardware. If the actual work uses classical exact enumeration or classical solvers, say “QUBO-based formulation” or “quantum-compatible formulation”; do not say that a quantum computer ran the experiment or that quantum advantage was demonstrated.

## Current public-facing wording

 > “CB-PFR is a proposed uncertainty-aware post-optimization selection layer with reproducible software and synthetic evaluation. An exploratory synthetic benchmark showed a conditional effect, but a subsequent preregistered confirmation did not meet its prespecified practical-effect threshold. A separate C5G7 UO₂/MOX layout-selection prototype tests a QUBO encoding. The current OpenMC C5G7 runs verify an exploratory integration path only; physical ranking effectiveness, direct burnup-QUBO-to-material mapping, and quantum advantage are not established.”

This is intentionally more precise than claiming that all physics and quantum requirements are already satisfied.
