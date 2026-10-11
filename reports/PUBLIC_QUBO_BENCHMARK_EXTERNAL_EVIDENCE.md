# External QUBO benchmark evidence: public recorded D-Wave comparisons

**Status: external-literature/data comparison added; no new QPU job submitted; no CB-PFR or reactor-physics benefit inferred.**

## Why this benchmark is included

The project has no authorized D-Wave API token available in its execution environment. Rather than fabricate a hardware run, this report records a public external benchmark that contains both QUBO instances and recorded solver outcomes. It is an alternative evidence source for contextualizing quantum-versus-classical optimization claims.

Primary public source:
- QUBO Solver Benchmark: https://www.qubos.org/
- Instance catalog: https://www.qubos.org/instances/
- Solver descriptions: https://www.qubos.org/solvers/
- Public repository README: https://github.com/ml-uhh/qubo-benchmark

The public benchmark describes 1,912 instances across graph-structured, random, spin-glass, and QPLIB families. Among 1,856 instances with results available for both the D-Wave Advantage and its classical reference solver, the published summary says the classical reference returned a lower objective value on 1,280 instances (69.0%) and the same objective value on 576 (31.0%). D-Wave has no returned result in the comparison for 56 additional instances. These counts and percentages are transcribed from the benchmark's published summary; this repository has not independently downloaded and rerun all 1,912 instances.

## What the comparison does and does not show

It is evidence that a public, recorded comparison exists and that the classical reference solver's returned objective was no worse than D-Wave's on the reported 1,856 matched instances. It is **not** a complete time-to-solution or quantum-advantage analysis because the aggregate objective comparison alone does not establish equal end-to-end runtime, equivalent tuning budgets, equal hardware/software resources, statistical uncertainty, or performance on reactor-loading instances.

The benchmark is not a nuclear fuel-management dataset, does not run CB-PFR, and does not validate a physical reactor model. It must not be described as a C5G7 experiment, an independent physical validation, or a reproduction of Usmanov et al.

## Recorded summary

The compact data transcription is stored in `config/benchmarks/public_qubo_benchmark_summary.csv`. The rows explicitly label the source as a published aggregate summary rather than trial-level measurements. Do not feed these aggregate counts to `scripts/analyze_solver_benchmark.py`, whose input contract requires repeated run-level trials.

## Relevance to CB-PFR

CB-PFR is a post-optimization selection/ranking layer, not a QUBO solver. A valid test of CB-PFR on external QPU results would require per-candidate objective/feasibility metrics and uncertainty estimates from the same fixed candidate pool, then a predeclared comparison of selection quality. The external summary here lacks those candidate-level fields, so it cannot estimate a CB-PFR treatment effect.

## Next reproducible step

1. Download and pin the public benchmark repository at a specific commit.
2. Inventory the actual per-instance files and recorded result format; hash the downloaded source.
3. Recompute the published matched-instance counts from the underlying records, preserving missing results.
4. Where raw per-run timing data exist, apply the repository's TTS analyzer only after checking that target quality and timing boundaries are comparable.
5. Keep the nuclear fuel-loading benchmark separate unless an identical mathematical QUBO and comparable raw trial data can be established.

## Claim boundary

Allowed: “We reviewed a public benchmark of recorded D-Wave and classical QUBO outcomes as external context.”

Not allowed from this aggregate summary alone: “CB-PFR improves QPU results,” “quantum advantage was demonstrated,” “D-Wave is slower on every problem,” or “the reactor-loading problem was physically validated.”

## References

- QUBO Solver Benchmark, https://www.qubos.org/
- Instances and source notes, https://www.qubos.org/instances/
- Solver implementations and recorded results, https://www.qubos.org/solvers/
- Repository, https://github.com/ml-uhh/qubo-benchmark
- Usmanov et al. (2024), *Quantum and quantum-inspired optimization for an in-core fuel management problem*, https://doi.org/10.1088/1742-6596/2701/1/012031
