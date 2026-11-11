# CB-PFR candidate-selection benchmark protocol (pre-registered)

**Status:** protocol specification; not a completed physical validation.
**Scope:** test whether uncertainty-aware post-optimization selection improves the quality of the selected candidate under an equal evaluation budget. This is distinct from validating the reactor-physics model.

## 1. Research question

Given a fixed candidate pool and a limited number of noisy evaluations per candidate, does CB-PFR select candidates with better reference-evaluated physical feasibility than (a) QUBO-energy-only ranking, (b) point-estimate ranking, and (c) a uniform-margin baseline?

## 2. Benchmark roles

1. **Primary method benchmark — controlled candidate-selection experiment.** Use a finite pool with a known or independently approximated reference outcome and injected/empirically estimated observation noise. This directly tests the selection layer. Synthetic tests are method verification, not reactor validation.
2. **Nuclear transport application benchmark — C5G7.** Use the six explicit UO2/MOX layout candidates already mapped to the model. Treat current 18-run data as smoke/exploratory only. Increase transport precision only after confirming convergence and a physically justified objective/acceptance rule.
3. **External physical validation — BEAVRS / appropriate evaluated experiments.** A validation dataset tests the simulator/observable/model. It does not by itself test CB-PFR's treatment effect. BEAVRS spatial comparison remains NOT_ESTABLISHED; do not promote it to the primary algorithmic benefit claim.
4. **ICSBEP.** Use only for a selected configuration whose benchmark specification is applicable and available under its access conditions. Criticality agreement alone does not establish fuel-loading ranking quality or detector-map agreement.

## 3. Freeze before confirmatory runs

Before confirmatory transport:
- Freeze candidate definitions, material/geometry mapping, code version, nuclear data, source revision, random-seed list, per-candidate tally definitions, uncertainty estimator, stopping rule, and analysis script.
- Define the primary physical objective and acceptable range with an authoritative source and units. Do not use the exploratory 0.98 synthetic threshold or previous illustrative C5G7 limits as reactor acceptance criteria.
- Use identical candidate pools and equal total transport/evaluation budgets for every selection procedure.
- Separate development seeds from confirmatory seeds. Never tune the mapping, orientation, limits, or risk coefficient on confirmatory results.
- Record every candidate, including failed, invalid, or excluded runs, with explicit reason and hashes.

## 4. Methods

Run these procedures on each identical candidate pool:
1. QUBO-only: lowest QUBO energy among QUBO-feasible candidates.
2. Point estimate: rank using observed metric means and nominal limits.
3. CB-PFR: use candidate-specific uncertainty bounds and the frozen lexicographic key.
4. Uniform-margin baseline: use a common margin selected on development data only.

If a procedure returns an invalid or physically infeasible candidate, count it as such; do not silently drop it. If no candidate is feasible, report the no-feasible-selection outcome.

## 5. Outcomes

**Primary outcome:** proportion of independent benchmark trials in which the selected candidate passes the predeclared reference-evaluated feasibility rule.

Secondary outcomes:
- reference-evaluated violation magnitude;
- regret relative to the best reference-evaluated candidate in the same pool;
- false-feasible selection rate (method says feasible, reference says infeasible);
- no-feasible-selection rate;
- total evaluation cost and number of reference evaluations;
- rank stability under seed resampling.

For a finite deterministic candidate set, evaluate all candidates at high precision for the reference ranking if computationally feasible. Otherwise, use a predeclared independent confirmation budget and propagate reference uncertainty rather than treating a noisy reference as truth.

## 6. Statistical analysis

- Pair methods within each candidate pool/seed block; report paired differences and 95% intervals.
- Use a trial-level bootstrap or an appropriate paired method, with the trial/pool—not each tally batch—as the independent unit.
- Report absolute rates, denominators, effect sizes, and uncertainty; do not report only p-values.
- Show results for all four methods and a sensitivity analysis for the predeclared operational bound parameter. Label exploratory sensitivity analysis as exploratory.
- A claimed benefit requires a positive paired difference for the primary outcome against both point-estimate and uniform-margin baselines, with uncertainty and all failures reported. If this gate is not met, state no demonstrated advantage.

## 7. C5G7-specific go/no-go gate

Current status: NO-GO for a high-budget confirmatory run until:
- the existing smoke results are independently reproduced from the committed artifacts;
- tally/mesh/material mappings and candidate IDs are audited;
- the objective and acceptance limits have authoritative justification;
- convergence is evaluated by increasing histories/batches and independent seeds;
- a pre-registered method-comparison script and equal-budget policy are committed.

After these checks, run development seeds first. Only proceed to confirmatory seeds if the physical outputs are stable enough to distinguish candidate differences from Monte Carlo uncertainty.

## 8. Claim boundaries

Permitted if artifacts support it:
- “CB-PFR is a proposed uncertainty-aware post-optimization selection method.”
- “In a synthetic benchmark under the specified data-generating process, CB-PFR achieved [measured result].”
- “The C5G7 integration pipeline executed [specified runs] under [specified conditions].”

Not permitted without new evidence:
- “CB-PFR is physically validated for reactor fuel loading.”
- “CB-PFR improves nuclear reactor performance/safety.”
- “The BEAVRS comparison validates CB-PFR.”
- “CB-PFR outperforms the baselines on physical candidates” unless the confirmatory comparison passes the gates above.

## References

- OECD/NEA C5G7-TD background and scope: https://oecd-nea.org/science/wprs/egrts/c5g7-td/
- OECD/NEA ICSBEP handbook scope and access: https://www.oecd-nea.org/jcms/pl_24498/international-criticality-safety-benchmark-evaluation-project-icsbep
- BEAVRS upstream model: https://github.com/mit-crpg/BEAVRS
- Current C5G7 gate report: reports/C5G7_CB_PFR_PHYSICAL_EFFECTIVENESS_GATE_2026-10-11.md
