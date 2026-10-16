# CB-PFR C5G7 convergence, equal-budget selection, and classical/QUBO experiments

Protocol dated 2026-10-16. Scope: six 2×2 fuel layouts with exactly two MOX and two UO₂ positions; five reflector positions fixed. All evidence is screening or algorithmic evidence, not safety certification, official benchmark acceptance, quantum advantage, or universal superiority.

## A. Trace-level convergence triage

The numerical triage cutoffs below were fixed for campaign-wide monitoring after preliminary spot-checks of a small artifact subset. Those preliminary runs are therefore not a blinded confirmatory test of the cutoffs; use them only as trace-review alarms, not as a formal hypothesis test or convergence certificate.

Operational screening cutoffs:
- At least 100 active trace values.
- Absolute first-half/second-half active k-generation mean shift ≤25 pcm.
- Absolute OLS k-generation slope ≤25 pcm per 1,000 active batches.
- Absolute first-vs-last-quarter entropy shift relative to mean entropy ≤0.1%.
- Absolute entropy slope relative to mean entropy ≤0.1% per 1,000 active batches.
- Raw HDF5 audit passes and zero fission-source-sites-outside-entropy-box warnings.

SCREEN_PASS means only that these operational alarms did not trigger. It is not a convergence certificate. Failed cases require trace review; extra inactive/active histories or mesh/source repairs depend on the failure cause. P6 is a deliberate bad-source stress run and is reported separately. V2a is a low-budget selection dataset, not high-budget physical truth.

## B. Equal-budget policy replay

The offline selector requires exactly 1,200 V2a run records and 60 P1–P4 high-budget records, with 200 complete six-layout seed pools and ten high-budget replicates per layout.

V2a settings: 800 batches, 500 inactive, 2,000 particles/batch. Pools 1–60 estimate between-seed variability; pools 61–200 are held out and grouped into 28 blocks of five. High-budget settings: 10,000 batches, 1,000 inactive, 10,000 particles/batch. UMMU high-budget replicates 1–5 define a relative operational threshold: mean + 2.132×SD/√5; replicates 6–10 for each layout define held-out empirical means. This is a noisy empirical reference, not ground truth.

Every policy receives 18 run-equivalents per decision. Compare equal allocation + point estimate, equal allocation + common uncertainty margin, equal allocation + candidate-specific uncertainty screen, and adaptive ranking-and-selection (six initial observations plus 12 allocations by lower confidence bound). Metrics: match to the held-out empirical reference best, mean/median regret in F_fission, baseline-screen pass rate, run count/allocation, and paired bootstrap 95% intervals versus point allocation.

F_fission = max(assembly-integrated fission rate)/mean(assembly-integrated fission rate) is a normalized fission-rate proxy, not absolute power or a safety metric. The screen is operational, not an approved physical limit. This is offline replay and launches no new OpenMC runs. Within-statepoint tally uncertainty is not propagated.

## C. Separate classical vs QUBO computation

Synthetic random quadratic binary instances: n=10,14,18; 30 instances per size; sum(x)=n/2. Each method receives 5,000 objective/energy evaluations per instance. Compare direct random search over feasible states with QUBO penalty A(sum(x)-n/2)^2 optimized via classical simulated annealing. A = 2×(sum absolute linear coefficients + sum absolute pair coefficients)+1. Exact enumeration supplies the objective-gap oracle but is not counted against the heuristic budget.

Metrics: oracle gap, feasibility, feasible-state fraction during QUBO search, exact-match rate, evaluation count, and wall-clock time. Equal evaluations do not equalize runtime or operations per evaluation. Simulated annealing is classical; no quantum hardware is used. These synthetic instances are not OpenMC physical results. The separate C5G7 four-variable penalty only enforces two MOX: all six feasible layouts have equal energy and cannot be physically ranked without a justified objective.

## D. Execution and reporting contract

The executable CI workflow is `.github/workflows/cbpfr-research-computational-experiments.yml`. It compiles the analysis scripts, runs the research experiment unit tests, and executes the frozen synthetic classical-versus-QUBO benchmark. The run artifact is the authoritative result record; this protocol text alone is not evidence that the experiment completed.

The campaign-wide OpenMC convergence screen and equal-budget policy replay are data-gated: they require the full, integrity-passing set of 75 production records, 1,200 V2a records, and 60 high-budget reference records. The workflow must report pending/incomplete rather than infer results from partial artifacts. Any flagged convergence cases are triaged before deciding whether to extend histories; no blanket rerun is authorized by this protocol.

Interpret solver results strictly as a comparison between two classical heuristics under equal objective/energy-evaluation budgets. No quantum hardware is involved, and no result from synthetic instances can be used as evidence of OpenMC physical superiority.
