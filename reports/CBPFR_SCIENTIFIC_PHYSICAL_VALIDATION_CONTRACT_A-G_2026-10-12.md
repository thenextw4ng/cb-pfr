# CB-PFR Scientific and Physical Validation Contract — A–G
**Decision date:** 2026-10-12  
**Scope:** CB-PFR / ReactorQ Studio, C5G7 four-fuel-position placement study  
**Purpose:** finish the research as a reproducible, scientifically defensible physical-validation study—not merely as software that runs.

**Current disposition: NOT YET PHYSICALLY VALIDATED.** Existing calculations support useful numerical and spatial-distribution evidence, but source/eigenvalue stationarity and independent model-specification sign-off remain open. This contract defines the evidence needed to close A–G; it does not predeclare that the evidence has passed.

## 1. Definition of done

The project has three separate milestones:

1. **Software-ready:** code and tests pass; workflows and evidence handling are reproducible.
2. **Scientific-ready for review:** physical model, numerical protocol, metrics, uncertainty, benchmark comparison, limitations, and manuscript are documented and auditable.
3. **Physically validated within a stated scope:** the actual model and tallies pass a justified, uncertainty-aware comparison with a compatible trusted benchmark; convergence and reproducibility are adequate; claims are limited to quantities and configurations actually tested.

The finish line is milestone 3 for the declared C5G7 benchmark quantities and tested configurations. Passing software CI is necessary but never sufficient. If evidence supports only a narrower claim, state that limitation instead of claiming full physical validation.

## 2. Frozen study boundary

- Enumerate six layouts over four fuel positions with exactly two UO₂ and two MOX assemblies; keep all five reflector positions fixed.
- Treat this as a C5G7 assembly-placement reformulation, not a direct reproduction of Usmanov's burnup-state QUBO.
- No quantum advantage, QPU execution, reactor-safety certification, absolute-power-in-watts claim, or validation of unmeasured quantities is implied.
- No new algorithm, metric, or experiment unless a documented scientific-validity blocker or an acceptance requirement makes it necessary.
- Never change acceptance limits after inspecting results. If a valid criterion was not specified in advance, mark the result exploratory and pre-register a justified protocol before collecting new data.

## 3. A–G scientific/physical acceptance gates

### A — Physical model identity, benchmark fidelity, and provenance
**Question:** Is the model actually transported a faithful, identified implementation of the intended C5G7 benchmark?

Required evidence:
- Exact upstream repository/commit, OpenMC version, actual generated geometry/material/settings/source inputs, boundary conditions, MGXS file and energy-group boundaries, environment, commands, logs, seeds, and hashes.
- Explicit comparison with the primary benchmark specification: geometry dimensions, assembly arrangement, material definitions, cross sections/group structure, boundary conditions, source/eigenvalue settings, and physical quantities to compare.
- A discrepancy register classifying every physics-significant difference as expected adaptation, justified implementation difference, or unresolved fidelity issue.
- Independent technical review/sign-off by a qualified reviewer, or an explicit limitation if unavailable.

**Pass only if** actual run inputs are traceable and all physics-significant deviations are resolved or justified. Matching hashes or matching upstream code alone does not prove physical fidelity.

### B — Geometry, tally semantics, and spatial mapping
**Question:** Do computed values correspond to the intended physical regions and quantities?

Required evidence:
- Verified mesh bounds, orientation, index ordering, assembly boundaries, tally filters/scores, bin-to-assembly map, units, volume treatment, and normalization from actual inputs/statepoints.
- Tests for indexing and data reduction plus a traceable map from every reported assembly value to its physical region.
- Comparison against a compatible trusted reference for the same quantity and region definition. If normalized fission-rate fractions are compared with published assembly power, justify the relationship and limit the claim to normalized spatial distribution.
- No relabeling integrated fission tallies as absolute power; no flux/pin-power claim without matching validated tallies.

**Pass only if** mapping is physically verified and a predeclared benchmark spatial quantity agrees within reference uncertainty and a justified acceptance rule. Visual similarity or a small post-hoc percentage difference alone is insufficient.

### C — QUBO, design-space, and physical-decision validity
**Question:** Does the mathematical problem encode permitted physical designs correctly, and does the decision rule select a physically defensible candidate?

Required evidence:
- Exhaustive enumeration of all six layouts; exactly two UO₂ and two MOX; reflector positions fixed; no duplicate/omitted layout.
- Direct calculation cross-checks of QUBO energy and constraints for every permitted layout and invalid test vectors.
- Explicit predeclared physical objective/feasibility rule stating how k-effective, normalized fission-rate distribution/peaking proxy, uncertainty, and physical constraints affect selection. Do not silently combine incomparable quantities.
- Candidate ranking must account for uncertainty and physical acceptability; a mathematical QUBO minimum alone is not a physical optimum.
- Evidence that the chosen layout's transport results are confirmed at sufficient precision. Screening-budget data alone support screening, not validated optimization.

**Pass only if** QUBO mapping is exact, the physical selection rule is approved before final rankings, and any claimed winner is supported by comparable transport evidence and uncertainty-aware separation—or is explicitly inconclusive.

### D — Experiment integrity, independence, reproducibility, and convergence
**Question:** Are runs traceable, genuinely replicated, and statistically suitable for physical conclusions?

Required evidence:
- Match each seed to statepoint, summary, settings, input hashes, MGXS, logs, and analysis outputs; verify completeness and integrity.
- Demonstrate the independence intended by the replication design. Distinct seeds/hashes are necessary but do not alone prove independent or stationary sampling.
- Review active-generation k traces, source-convergence diagnostics, entropy traces where applicable, and run-to-run variation. Use a scientifically justified criterion or qualified expert interpretation; do not invent a threshold after seeing traces.
- Report within-run Monte Carlo uncertainty separately from between-seed variation and explain disagreement.
- Repeat transport only if current evidence is technically invalid or cannot answer a predeclared question; never rerun to obtain a preferred outcome.

**Pass only if** artifacts are intact and convergence/replication evidence supports precision and stationarity assumptions. A successful analysis workflow does not certify convergence.

### E — Uncertainty-aware physical benchmark validation
**Question:** Do computed physical quantities agree with the selected trusted benchmark at a defensible level, including numerical uncertainty?

Required evidence:
- Identify the primary benchmark and any secondary published reference, exact configuration, reported quantity, normalization, uncertainty, and applicability to the adapted geometry.
- Predeclare acceptance criteria for k-effective, spatial distribution, uncertainty, convergence, and other reported quantities. Separate internal screens from official benchmark criteria.
- Report per-run means/uncertainties, combined-uncertainty assumptions, between-seed variation, normalized spatial differences, residuals, and pass/fail/inconclusive outcomes.
- Compare like with like. Scalar k-effective agreement cannot compensate for invalid spatial mapping or a model-specification mismatch.
- Any quantity without a compatible reference remains exploratory, not physically validated.

**Pass only if** the predeclared, physically justified protocol is satisfied for every quantity included in the validation claim. If convergence is unresolved or the reference is incompatible, this gate remains blocked even if central values agree.

### F — Fail-closed scientific evidence pipeline
**Question:** Can the workflow prevent incomplete or scientifically inadequate evidence from being mistaken for validation?

Required evidence:
- CI on the exact release commit; tests for missing/corrupt artifacts, mismatched hashes/settings, missing diagnostics, invalid layout/QUBO, invalid mapping metadata, and unapproved physical objective.
- The pipeline must distinguish SOFTWARE_PASS, NUMERICAL_SCREEN_PASS, PHYSICAL_VALIDATION_PASS, INCONCLUSIVE, and FAIL. It must not infer physical validation from a green test suite or one scalar tolerance.
- Validation must fail closed if model-fidelity review, convergence evidence, reference compatibility, or required spatial checks are absent.
- Run the repaired analysis/recovery workflow end-to-end on preserved data; report production-transport workflow status separately.

**Pass only if** the exact release candidate passes CI and the evidence pipeline enforces scientific blockers. CI success alone never closes A–E.

### G — Scientific synthesis, bounded claims, and release
**Question:** Does the final package communicate what the physics evidence establishes—and no more?

Required evidence:
- Final evidence matrix for A–F with statuses, artifacts, commit IDs, criteria, reviewer decisions, and unresolved risks.
- Reproducible tables/figures for all six screening layouts, canonical confirmation, uncertainty, convergence, and benchmark comparisons.
- Methods/results/discussion/UI/docs agree on model identity, score semantics, uncertainty, selection rule, and limitations.
- Explicit separation between software-tested, numerically screened, benchmark-compared, and physically validated claims.
- Reproduction package with pinned source, run configuration, analysis outputs, hashes, commands, and interpretation notes.

**Pass only if** every physical-validation claim traces to passed A–F evidence; unresolved items are labelled and do not support affirmative claims. If a required gate fails, report failed/inconclusive research rather than calling it physically validated.

## 4. Current evidence and blockers (2026-10-12)

Evidence already recorded:
- Three high-budget canonical UMMU runs exist (seeds 720000, 730000, 740000; 7,000 batches, 500 inactive, 10,000 particles/batch), with preserved statepoints and raw HDF5 audits.
- Raw HDF5 audits passed 22/22 checks per run; artifact hashes and common MGXS/group structure were checked.
- Canonical mean k-effective = 1.1864932118; difference from reference target 1.18655 is −5.679 pcm; combined-uncertainty z ≈ −0.434; maximum reported within-run SD is 9.698 pcm. These pass provisional internal scalar screens only.
- A published-reference comparison of normalized four-position spatial distribution is recorded with maximum relative difference 0.179%. It supports only the stated normalized distribution comparison, not absolute watts, flux, or other tallies.
- Recovery workflow successfully generated diagnostics from saved statepoints and ran the repository aggregator without rerunning transport. The workflow repair PR remains separate from main until reviewed/merged.

Open blockers that prevent physical-validation completion:
1. **A:** independent sign-off on fidelity to the primary C5G7 benchmark specification and resolution of physics-significant model/group-structure/source differences.
2. **D/E:** source/eigenvalue stationarity is not certified. Recovered generation traces show first-to-last-quarter shifts of +42.06, +65.05, and +23.99 pcm; exploratory trend tests are not proof of stationarity. Obtain qualified review or predeclare a justified follow-up protocol.
3. **C/E:** six-layout results are screening-budget data; only UMMU has the current high-budget confirmation. Approve the physical objective/acceptance band before claiming a winner; confirm candidates at comparable precision if the claim requires ranking among them.
4. **B/E:** keep spatial claims limited to the normalized distribution comparison currently supported; no absolute-power/flux claim without compatible tallies and references.
5. **F/G:** review and merge workflow repair through normal repository process, then verify final release commit and archive CI/evidence outputs.

## 5. Stop rule and permitted follow-up

Do not expand scope. Permitted work is limited to closing explicit A–G blockers: model-specification review, convergence review/protocol, objective approval, required confirmation calculations, workflow repair/verification, or release documentation. No cosmetic refactor or new metric/algorithm.

Do not launch another expensive transport run until the convergence reviewer/protocol specifies why existing traces are inadequate, which settings must change (if any), what quantity will be judged, and what predeclared result constitutes adequate evidence. Preserve current results and record the protocol before execution.

## 6. Final status rule

The project may be labelled **scientific-ready for independent validation review** when evidence packages and reviews are prepared. It may be labelled **physically validated** only after applicable A–F gates pass and G's claim audit is complete. Current status remains **NOT YET PHYSICALLY VALIDATED**.

## References and linked evidence

- Current evidence closeout: https://github.com/thenextw4ng/cb-pfr/blob/feature/scientific-readiness-a-g-hardening/reports/CBPFR_A-G_EVIDENCE_CLOSEOUT_2026-10-12.md
- Original high-budget transport run: https://github.com/thenextw4ng/cb-pfr/actions/runs/38196703024
- Recovered analysis run: https://github.com/thenextw4ng/cb-pfr/actions/runs/38207010156
- Workflow repair PR: https://github.com/thenextw4ng/cb-pfr/pull/50
- Scientific readiness PR: https://github.com/thenextw4ng/cb-pfr/pull/49
- OECD/NEA C5G7 benchmark: https://www.oecd-nea.org/jcms/pl_13548/benchmark-on-deterministic-transport-calculations-without-spatial-homogenisation
- Published C5G7 assembly/pin-power comparison: https://www.frontiersin.org/journals/energy-research/articles/10.3389/fenrg.2020.00124/full
- Pinned model source: https://github.com/mit-crpg/benchmarks/tree/ba41bee54320ada0b4ac39a0dd2ca3c1d090a450
