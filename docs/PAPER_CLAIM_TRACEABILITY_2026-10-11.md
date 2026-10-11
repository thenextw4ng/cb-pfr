# Paper claim traceability — ReactorQ / EUREKA! and CB-PFR

**Audit date:** 11 October 2026  
**Scope:** the supplied EUREKA! ITB 2026 project paper and the CB-PFR methodological working paper.  
**Purpose:** close the evidence inventory without converting missing evidence into a scientific claim.

## Decision

The code-and-evidence audit is reproducible, but the full scientific claims are **not all closed**. Existing OpenMC runs establish that transport calculations executed and that selected structural audits passed. They do not, by themselves, establish that the Usmanov burnup-state QUBO was physically mapped to C5G7, that the C5G7 benchmark was reproduced and accepted, or that a physical reactor experiment validated the result.

## EUREKA! paper claims

| Paper claim | Current evidence | Status | What would close it |
|---|---|---|---|
| QUBO formulation and feasible fuel configurations | Exact enumeration of a separate four-position C5G7 layout QUBO; six assignments satisfy the two-UO2/two-MOX constraint | **PASS — software formulation only** | Keep the separate model identity explicit; do not call it the Usmanov burnup QUBO |
| Physical transport simulation ran | OpenMC 0.16.0 executed 18 exploratory cases, six layouts × three seeds; group-structure and spatial-mapping audits passed | **PASS — execution only** | Primary-specification review and convergence/acceptance protocol |
| \(k_{\mathrm{eff}}\) recorded and compared | Low-budget three-seed mean for UMMU is 1.18610263; reference screen is recorded | **SCREEN ONLY** | Completed convergence study, reviewed model identity, and predeclared acceptance criteria |
| Neutron-flux distribution obtained | Existing evidence inventory supports \(k_{\mathrm{eff}}\) and an assembly-integrated fission-rate proxy; a reviewed flux-distribution result is not established | **NOT ESTABLISHED** | Produce and audit the actual flux tally/mesh, normalization, uncertainty, and spatial plots |
| Power-peaking factor compared with reference | Local observable is maximum assembly-integrated fission rate divided by the four-assembly mean; reference 2.498 is maximum normalized pin power | **BLOCKED — unlike observables** | Obtain a matched pin-power/assembly-power reference and matching tally/normalization |
| Repeated quantum-annealing runs, solution frequencies, Hamming distances | Three OpenMC seeds per layout are transport replicates, not optimizer samples; no actual quantum-annealing execution is evidenced | **NOT RUN** | Run the stated annealer on the documented QUBO, preserve raw samples/solver metadata, then calculate frequencies and pairwise Hamming distances |
| Usmanov burnup states mapped to the physical reactor model | No defensible mapping from fresh/once-burned/twice-burned labels to the UO2/MOX C5G7 categories | **BLOCKED** | Document the exact depletion/material states, isotopic compositions and history, and obtain independent reactor-physics review; otherwise present the C5G7 study as a separate formulation |
| Benchmark-grade convergence and acceptance | The preserved high-budget run was cancelled after two seeds; the aggregate gate was skipped and entropy-box warnings remain in that artifact | **BLOCKED** | Corrected high-budget runs, reviewed convergence diagnostics, full model identity review, and predeclared acceptance criteria |
| Experimental physical validation | A computational benchmark is not a physical-reactor experiment; no comparable experimental dataset is established | **NOT ESTABLISHED** | A genuinely comparable experiment, provenance, measurement uncertainty, and a reviewed validation protocol |

## CB-PFR working-paper claims

| Claim | Current evidence | Status | Interpretation |
|---|---|---|---|
| CB-PFR ranking implementation exists | src/cbpfr/ranking.py, integration layer, tests and CI | **PASS — software** | Implementation of a proposed ranking rule does not establish physical utility |
| Synthetic comparison benchmark | 1,000 trials; committed aggregate rates: QUBO-only 0.857, point estimate 0.933, CB-PFR 0.976, uniform margin 0.966; CI reproduces the aggregate | **PASS — synthetic protocol** | Conditional on the benchmark's data-generating process; not a physical result and not universal superiority |
| Independent full reproduction of all synthetic trials | The recorded audit explicitly says independent_full_rerun is false; CI reproduces the aggregate protocol | **PARTIAL** | Describe as repository-reproduced aggregate, not an independent replication |
| CB-PFR validated on physical C5G7 results | No approved design-specific limits, no defensible legacy QUBO mapping, and the current physical observable is only an exploratory proxy | **BLOCKED** | Need physically justified limits and source-comparable data before claiming physical feasibility selection |
| CB-PFR establishes reactor safety or universal superiority | No evidence supports either claim | **NOT CLAIMED** | Keep these claims out of the abstract, conclusion, and metadata |

## Recorded numerical evidence

- Six C5G7 layout signatures were each evaluated with three independent seeds at 100 batches, 10 inactive batches, and 1,000 particles per batch.
- For UMMU, the recorded mean \(k_{\mathrm{eff}}\) is 1.18610263; between-seed sample SD is 0.00386340 and the standard error of the mean is 0.00223053 for three runs.
- The published reference \(k_{\mathrm{eff}}=1.18655\pm0.000095\) is used only as a numerical screen because model identity and benchmark-grade convergence have not been signed off.
- The six-layout smoke artifact contains aggregate flux tally values; this is evidence that the tally ran, not a validated flux distribution. The mean assembly-integrated fission-rate peaking proxy for UMMU is 1.886113, with between-seed sample SD 0.028995. It is not comparable to the published maximum normalized pin power 2.498.
- The synthetic CB-PFR aggregate reports selected true-feasibility rates of 0.857, 0.933, 0.976 and 0.966 for QUBO-only, point-estimate, CB-PFR and uniform-margin methods, respectively. These are synthetic benchmark results only.

## Reproducibility

Run the audit from the repository root:

    python scripts/audit_paper_claims.py --out /tmp/paper-claim-audit.json
    python -m unittest tests.test_paper_claim_audit -v

The audit is fail-closed on artifact-integrity inconsistencies. Its overall status is AUDIT_COMPLETE_WITH_OPEN_SCIENTIFIC_BLOCKERS: this means the claim inventory is reproducible, **not** that all scientific claims are validated.

## Final rule for manuscript language

Do not claim actual quantum-annealing runs unless the solver execution and raw samples exist. Do not claim flux distribution without an audited flux tally. Do not compare assembly-integrated fission rate to normalized pin power as though they were the same quantity. Do not call the C5G7 study a validated physical mapping of the Usmanov burnup-state QUBO. Do not call synthetic CB-PFR results physical validation. These distinctions preserve the credibility of both manuscripts.
