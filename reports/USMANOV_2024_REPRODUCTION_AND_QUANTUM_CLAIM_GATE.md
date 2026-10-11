# Usmanov et al. (2024): reproduction plan and quantum-claim gate

**Status: benchmark harness added; reproduction not yet run; quantum advantage not established.**

## Source and what it actually contains

S. R. Usmanov, G. V. Salakhov, A. A. Bozhedarov, E. O. Kiktenko, and A. K. Fedorov, “Quantum and quantum-inspired optimization for an in-core fuel management problem,” *Journal of Physics: Conference Series* 2701 (2024) 012031. DOI: [10.1088/1742-6596/2701/1/012031](https://doi.org/10.1088/1742-6596/2701/1/012031); preprint: [arXiv:2308.13348](https://arxiv.org/abs/2308.13348). The paper is open access under CC BY 3.0.

The paper studies QUBO fuel-reloading patterns and reports experiments with a D-Wave Advantage quantum annealer, a SimCIM emulator, and a classical simulated-annealing implementation. The tested core sizes and fresh/once-burnt/twice-burnt counts in Table 1 are transcribed into `config/benchmarks/usmanov_2024_core_instances.csv`.

**Critical limitation:** this published paper does not supply the complete raw per-trial sample set, device job records, all timing components, and exact software/environment needed to independently re-estimate its full uncertainty and wall-clock quantum-vs-classical comparison from raw data. Its reported aggregate time-to-solution figure is useful prior literature, not a substitute for a fresh, fair reproduction. The paper itself concludes that practical advantage had not yet been reached.

The word “real” in its “real nuclear core configurations” refers to reactor-core configurations represented in the optimization model; it must not be misreported as new experimental measurements of an operating reactor. The paper explicitly identifies the addition of real reactivity parameters and flux calculation as future work.

## What this repository now provides

`scripts/analyze_solver_benchmark.py` is a standard-library-only analyzer for new repeated solver trials. It reports, per instance and method:

- observed target-solution success probability and 95% Wilson interval;
- repetitions estimated for a declared target probability (default 99%);
- time-to-solution using per-attempt wall time **plus one-time setup cost**;
- device-only anneal-time TTS separately, so it cannot be silently substituted for end-to-end time;
- an uncertainty range obtained by transforming the Wilson interval.

It rejects duplicate trial IDs, invalid times, and inconsistent setup-time accounting. Unit tests cover the key logic. The analyzer does not claim advantage merely because a solver is quantum or has a short anneal time.

## Run-level data contract

For each `instance_id × method`, provide repeated independent trials with these CSV columns:

```csv
instance_id,method,trial_id,success,per_attempt_wall_time_s,one_time_setup_s,anneal_time_s,objective_value,feasible
```

- `success` must mean the same predeclared target solution quality/feasibility for every method on the same instance.
- `per_attempt_wall_time_s` must include the declared per-run overhead; explain any excluded queueing or cloud latency.
- `one_time_setup_s` must include the declared model construction, embedding, compilation, and initialization costs and remain constant within each instance/method group.
- Preserve every trial, including failures. Do not infer success from a solver's own status unless the returned bitstring is independently checked against the same constraints.
- Record hardware/device model, solver/library version, seeds, QUBO coefficients, embedding and chain-break policy, reads, anneal schedule, CPU/GPU model, thread count, and exact target energy/constraint rule in the accompanying manifest.

## Reproduction protocol

1. **Freeze the mathematical instance.** Recreate the published 13, 37, 69, 97, 121, 193, and 241-cell constraints and counts from the paper and archive the exact QUBO matrices, constants, variable ordering, and feasibility checker. Do not compare different QUBOs under the same instance label.
2. **Validate formulation.** Independently test all hard constraints on returned bitstrings. For small instances, compare against exact enumeration or a MILP/CP-SAT reference where practical.
3. **Run repeated trials.** Use a predeclared number of independent seeds/runs for D-Wave (if credentials/device access are available), a strong classical baseline, and any quantum-inspired solver. Match the target criterion and stopping rule.
4. **Measure all relevant cost.** Report device anneal time and end-to-end wall time separately. Include programming, embedding, sampling, decoding, feasibility repair, and repeated calls as applicable. Report queue/remote latency separately rather than silently omitting it.
5. **Estimate uncertainty.** Use success-probability intervals and repeated-run variability; do not claim an advantage from a single lucky sample or only the physical anneal microseconds.
6. **Predeclare the decision rule.** A quantum-advantage statement requires a reproducible, statistically defensible advantage on a meaningful metric against appropriate classical baselines, with the compared solution quality and resource boundary stated. A speedup only in device time must be named “device-time speedup,” not end-to-end quantum advantage.
7. **Keep physics validation independent.** Algorithmic feasibility in the published heuristic QUBO does not validate reactor physics. A physical claim requires a justified material/burnup mapping, validated response model, benchmark comparison, uncertainty propagation, and evidence that CB-PFR changes selection outcomes beneficially.

## Current claim decision

- **Allowed:** “This project uses a QUBO formulation inspired by published in-core fuel-management benchmarks.”
- **Allowed after exact instance recreation and a run:** “We reproduced the declared mathematical benchmark under the stated software/hardware protocol,” with full artifacts.
- **Not currently allowed:** “We demonstrated quantum advantage,” “quantum computing is faster for this reactor problem,” or “CB-PFR improves reactor physics.”
- **Not currently allowed:** calling the published optimization study “experimental reactor measurement data.”
- **Possible future claim:** a bounded physical improvement for a named benchmark and metric, only if the independent physical validation and controlled comparison gates pass.

## Reproducible analyzer

```bash
python scripts/analyze_solver_benchmark.py --input results/solver_trials.csv --output results/solver_tts_summary.csv --target-probability 0.99
```

The workflow is intentionally fail-closed: no raw trial data means no reproduction claim, and no device job records means no quantum-hardware execution claim.
