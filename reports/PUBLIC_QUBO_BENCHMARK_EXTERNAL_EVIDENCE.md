# External QUBO benchmark evidence: public recorded D-Wave comparisons

**Status: public external benchmark inspected and transcribed; no new QPU job submitted; no CB-PFR or reactor-physics benefit inferred.**

## Why this benchmark is included

The project has no authorized D-Wave API token available in its execution environment. Rather than fabricate a hardware run, this report records a public external benchmark containing QUBO instances and recorded solver outcomes. It provides an empirical external comparison for contextualizing solver claims.

Primary source repository: [ml-uhh/qubo-benchmark](https://github.com/ml-uhh/qubo-benchmark). The source was inspected at commit `68ab9f51e4af928088cf1bccd57a6c25fa68bcac` (main, 2026-09-06). This pins the source revision for future independent download/reanalysis.

## Recorded objective comparison

The source README reports 1,912 instances across four families. For 1,856 instances with results from both D-Wave Advantage and the classical reference solver, the classical reference returned a lower objective on 1,280 cases (69.0%), the same objective on 576 (31.0%), and D-Wave returned no result for 56 additional instances. The source reports no instance where D-Wave returned a strictly lower objective than the classical reference in this comparison.

| Instance family | Total | Classical lower | Equal | D-Wave lower | D-Wave result missing |
|---|---:|---:|---:|---:|---:|
| compsup | 480 | 80 | 360 | 0 | 40 |
| random | 23 | 13 | 7 | 0 | 3 |
| s28-qac | 1,386 | 1,177 | 200 | 0 | 9 |
| QPLIB | 23 | 10 | 9 | 0 | 4 |
| **All** | **1,912** | **1,280** | **576** | **0** | **56** |

These are source-reported aggregate objective outcomes, transcribed into `config/benchmarks/public_qubo_benchmark_summary.csv`. The project has inspected the upstream README and repository structure, but has **not** independently downloaded, rerun, or reconstructed all 1,912 instances. The table is therefore external published evidence, not an independent reproduction by this project.

## What the comparison does and does not show

It shows that this particular public benchmark's recorded classical reference objective was no worse than D-Wave's on the reported matched instances. It does **not** prove classical solvers are universally better, and does not establish a fair end-to-end runtime or quantum-advantage comparison. Objective quality, time-to-solution, embedding failures, solver settings, time budgets, hardware/software boundaries, and uncertainty must be analyzed separately.

The benchmark covers graph-structured, random, spin-glass, and QPLIB QUBOs. It is not a nuclear fuel-management dataset, does not run CB-PFR, and does not validate a physical reactor model. It must not be described as a C5G7 experiment, independent nuclear validation, or a reproduction of Usmanov et al.

## Relevance to CB-PFR

CB-PFR is a post-optimization selection/ranking layer, not a QUBO solver. A valid CB-PFR test on QPU-generated candidates needs per-candidate metrics and uncertainty estimates from the same fixed candidate pool, then a predeclared comparison of selected-candidate quality. This external aggregate table lacks those candidate-level fields and cannot estimate a CB-PFR treatment effect.

## Next reproducible step

1. Download the upstream repository at the pinned commit above and record archive/file hashes.
2. Inspect the raw per-instance records and reconstruct the README's family-level counts, including missing results.
3. Check which source files contain comparable per-run timing data; do not derive TTS from aggregate objective counts.
4. If timing data are sufficient, compare only matched instances and explicitly separate solver time, embedding/setup, remote latency, and total wall time.
5. Keep this general QUBO benchmark separate from nuclear fuel-loading evidence unless the same mathematical instances and comparable raw trial data can be established.

## Claim boundary

Allowed: “We inspected a public benchmark of recorded D-Wave and classical QUBO objective outcomes as external context.”

Not supported by this table alone: “CB-PFR improves QPU results,” “quantum advantage was demonstrated,” “classical solvers always outperform quantum hardware,” or “the reactor-loading problem was physically validated.”

## References

- [QUBO Solver Benchmark repository](https://github.com/ml-uhh/qubo-benchmark), pinned at `68ab9f51e4af928088cf1bccd57a6c25fa68bcac`.
- [QUBO benchmark README](https://github.com/ml-uhh/qubo-benchmark/blob/68ab9f51e4af928088cf1bccd57a6c25fa68bcac/README.md).
- [Instance catalog](https://www.qubos.org/instances/) and [solver descriptions](https://www.qubos.org/solvers/).
- Usmanov et al. (2024), *Quantum and quantum-inspired optimization for an in-core fuel management problem*, https://doi.org/10.1088/1742-6596/2701/1/012031.
