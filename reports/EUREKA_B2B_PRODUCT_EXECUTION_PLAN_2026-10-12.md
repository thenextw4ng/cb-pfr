# CB-PFR / ReactorQ Studio — B2B product execution plan
Date: 2026-10-12
Repository: thenextw4ng/cb-pfr
Working branch: feature/eureka-demo-dashboard

## Product thesis
CB-PFR is the research method: an uncertainty-aware post-optimization candidate-ranking layer. ReactorQ Studio is the product wrapper: a traceable scientific workflow for candidate intake, QUBO/optimizer outputs, physics-evaluation evidence, uncertainty-aware ranking, comparison, and reproducible reporting. The product must not conflate the method with OpenMC, QUBO, or nuclear-safety certification.

## Current evidence boundary
- Supported: CB-PFR implementation and tests; synthetic benchmark infrastructure; explicit QUBO encodings; a C5G7/OpenMC integration smoke workflow; reproducible repository/CI artifacts.
- Not established: physical effectiveness of CB-PFR; a defensible mapping from the legacy burnup-state QUBO to C5G7 UO2/MOX; successful spatial validation against BEAVRS; quantum-device execution or quantum advantage.
- The 40,000-pool confirmatory synthetic experiment did not meet its predeclared >=2 percentage-point practical-effect threshold. This must remain visible in product copy and scientific reporting.
- The current C5G7 smoke used illustrative limits and low-budget settings; it is pipeline evidence, not an engineering acceptance or safety result.

## Ten-step execution sequence
1. Audit the repository, evidence, product surfaces, and open scientific claims.
2. Build a versioned evidence catalog: public experimental/benchmark/simulation datasets, licenses, provenance, uncertainty, hashes, and known limitations.
3. Define the BRIN-facing use case around published Indonesian reactor/neutronics research. State scientific relevance only; do not imply endorsement, partnership, or adoption without written confirmation.
4. Freeze CB-PFR mathematical specification, implementation invariants, and novelty/related-work audit.
5. Standardize the optimization interface: QUBO/candidate pool -> explicit feasibility checks -> versioned evaluation records; keep unrelated encodings separate.
6. Run validation experiments with predeclared observables, acceptance criteria, independent repeats, common budgets, and baseline comparisons.
7. Add reliability, sensitivity, ranking stability, uncertainty-provenance, and failure-case reports; synthetic and physical evidence must be separate.
8. Deliver a professional interactive UI driven by real repository artifacts, with clear status labels and downloadable reports.
9. Make clean-checkout reproducibility, tests, provenance, documentation, and artifact audits release gates.
10. Package EUREKA demo and a B2B pilot kit: defined user problem, reproducible demo, technical one-pager, limitations, and pilot evaluation plan.

## What can be executed immediately without the user's Mac
- Repository/code/report audit through GitHub.
- Build product information architecture and dashboard features using committed result files.
- Add tests, static checks, parsers, data-contract validators, reproducibility checks, and documentation.
- Run synthetic benchmarks and lightweight QUBO enumerations on GitHub Actions.
- Run archived-statepoint analyses if the committed artifacts are sufficient.
- Launch the existing BEAVRS/OpenMC workflow through workflow_dispatch when the repository's Actions interface/permissions are available; it has a 360-minute timeout and uses substantial compute. A workflow launch must be verified by a real run URL before describing it as running.
- Do not launch a long OpenMC transport merely for visual impact. First verify the model/data temperature, detector operator, benchmark state, tally observable, and acceptance criteria.

## Immediate execution order
A. Keep main untouched; work only on feature/eureka-demo-dashboard.
B. Audit existing dashboard entrypoint/pages and the CI contract.
C. Make one product-facing, testable improvement at a time; use CI as a regression gate.
D. Run lightweight and synthetic validations first. Run high-budget OpenMC only after the protocol and model inputs are frozen.
E. Preserve failed or inconclusive results and show them in the dashboard; never turn a pipeline pass into a physical-validation claim.

## Product acceptance gates
1. Scientific: every result links to source data, settings, code revision, uncertainty definition, and acceptance rule.
2. Technical: clean install, automated tests, stable data contracts, reproducible output, and useful failure messages.
3. Product: workflows are understandable to a research user, charts come from evidence, exports are downloadable, and synthetic/archived/experimental sources are unmistakably distinguished.
4. Pilot: a real research workflow and evaluation criteria are identified before claiming B2B readiness.

## Initial dashboard information architecture
- Overview: project state, recent runs, evidence status, open validation gates.
- Candidate Explorer: candidate definitions, constraints, and provenance.
- Optimization: QUBO formulation, constraints, solver type, runtime, energy and feasibility.
- Physics Evidence: k-effective, fission-rate observables, tally uncertainty, model/data provenance.
- Reliability Lab: CB-PFR vs baseline, repeated-run stability, sensitivity, paired uncertainty.
- Decision Report: selection rationale, trade-offs, abstentions, and limitations.
- Evidence & Reproducibility: run manifests, hashes, workflow links, artifacts, environment, and export.

## Non-negotiable language
Use “QUBO-based” or “quantum-inspired/classical simulated quantum annealing” when that is what ran. Do not claim QPU execution, quantum advantage, physical validation, reactor safety, BRIN partnership, or a physical CB-PFR treatment effect without corresponding direct evidence.
