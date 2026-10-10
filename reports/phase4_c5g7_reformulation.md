# Phase 4 — Explicit C5G7 design-space reformulation

## Decision

The legacy abstract burnup-state QUBO is **not** mapped to C5G7. Instead, the optimization problem is explicitly reformulated in C5G7's own assembly-material vocabulary. This is a distinct design study, not a claim that the OECD/NEA reference benchmark itself is an optimization benchmark.

The public MIT CRPG 2-D model builder describes a 3×3 lattice with a 2×2 fuel block and reflector assemblies. Its canonical fuel-block arrangement is:

```text
UO2  MOX  reflector
MOX  UO2  reflector
reflector reflector reflector
```

Source implementation: https://github.com/mit-crpg/benchmarks/blob/master/c5g7/openmc/2d/build-xml-2d.py  
Primary benchmark description: https://www.oecd-nea.org/jcms/pl_13548/benchmark-on-deterministic-transport-calculations-without-spatial-homogenisation

The source model and the primary specification must still be checked together before a benchmark-verification claim. Noncanonical arrangements below are **variants of the source model**, not official C5G7 reference cases.

## New decision variables

Let the four fuel assembly positions be (P=\{p_{00},p_{01},p_{10},p_{11}\}). Let (m\in\{U,M\}) denote UO2 or the source model's MOX material family. Define binary assignment variables:

[
y_{p,m}=\begin{cases}1,&\text{if material family }m\text{ is assigned to position }p,\\0,&\text{otherwise.}\end{cases}
]

The assignment constraints are:

[
y_{p,U}+y_{p,M}=1\quad\forall p\in P,
]

[
\sum_{p\in P}y_{p,M}=2,\qquad \sum_{p\in P}y_{p,U}=2.
]

A QUBO feasibility energy is:

[
H_{\mathrm{feas}}(y)=A\sum_{p\in P}(y_{p,U}+y_{p,M}-1)^2
+B\left(\sum_{p\in P}y_{p,M}-2\right)^2,
]

where (A,B>0). Since variables are binary, this is a quadratic unconstrained binary objective after expansion. It encodes assignment/count constraints only; **it does not encode reactor physics**.

## Why physics is an outer evaluation

A physically meaningful objective such as minimizing assembly/pin power peaking cannot be assigned trustworthy QUBO coefficients before a transport response has been computed or a validated response surrogate has been trained. No arbitrary coefficients are inserted.

The initial design space has only:

[
\binom{4}{2}=6
]

unique placements of two UO2 and two MOX assemblies in four positions. Thus the correct first experiment is exhaustive enumeration, not quantum annealing. This creates a transparent ground-truth comparison for future heuristics. Each candidate must be built from the upstream geometry/material definitions and run with the same verified nuclear data, settings, tallies, and statistical protocol. The canonical source arrangement is retained as a baseline identity check.

A future physics objective must be declared before inspecting candidate outcomes. Candidate-level output should include at minimum:
- effective multiplication factor and its Monte Carlo statistical uncertainty;
- the benchmark-compatible assembly/pin power or fission-rate distribution and uncertainties;
- convergence diagnostics and run settings;
- source revision, input hashes, nuclear-data provenance, and runtime;
- explicit comparison against the canonical baseline and applicable primary reference quantities.

The exact objective and constraints must be chosen only after confirming which tallies and reference data apply to the selected source case. No keff, flux, power, feasibility, or winner is fabricated by this design-space generator.

## Reproducible enumeration

Run from the repository root:

```bash
python scripts/enumerate_c5g7_layouts.py --output results/c5g7_design_space.json
```

The CLI refuses to overwrite an existing output and emits a deterministic JSON manifest containing six unique candidates, the canonical baseline identity, fixed reflector positions, constraints, and explicit empty physical-results fields. It does not require OpenMC and does not run transport.

The standalone tests are:

```bash
python -m unittest tests.test_c5g7_layout_enumeration -v
```

(If the tests directory is not a Python package, run the repository-wide discovery command instead: `python -m unittest discover -s tests -v`.)

## Scientific boundary and relationship to CB-PFR

This reformulation resolves the **decision-variable/material-label mismatch** by defining a new C5G7 assembly-placement problem. It does not retroactively validate the legacy seven-position `fresh/once_burned/twice_burned` QUBO. The legacy model remains an abstract optimization example and must be described separately.

The new design space is ready for implementation against a verified transport model; physical evaluation is not complete until compatible model inputs and cross sections are available, a run actually completes, and its results are compared with the primary benchmark specification. CI passing only validates the enumerator and its safety tests.

## Status

- [x] Explicitly define new decision variables and material categories.
- [x] Define QUBO feasibility penalty for assignment/count constraints.
- [x] Enumerate all six feasible layouts and preserve the canonical reference layout.
- [x] Make the output deterministic and fail-safe.
- [ ] Instantiate and review the exact OpenMC model/input provenance.
- [ ] Execute baseline transport case and compare with primary benchmark values.
- [ ] Evaluate all six layouts with predeclared physical metrics.
- [ ] Analyze repeated-run uncertainty and feed evidence into CB-PFR.
