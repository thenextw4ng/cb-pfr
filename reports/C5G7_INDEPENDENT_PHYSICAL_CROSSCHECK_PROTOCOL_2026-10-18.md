# Independent C5G7 physical cross-check protocol

**Protocol date:** 2026-10-18  
**Status:** prospective; launched through GitHub Actions. Results must be interpreted from the generated machine-readable report, not from workflow success alone.

## Question
Does the canonical UO2/MOX layout in the CB-PFR OpenMC model produce neutronic response consistent with public C5G7 benchmark values and an independently implemented deterministic transport solver, and does the P4/P5 held-out comparison support a limited CB-PFR ranking claim?

This protocol separates three claims that must not be conflated:
1. **Benchmark consistency:** canonical UMMU response is compared with the published 2-D C5G7 (k_{eff}) reference and pin-power summary.
2. **Independent-code cross-check:** the OpenMC normalized pin fission-rate map is compared to a separately implemented S_N transport solver at the same canonical layout. Its output is a code-to-code comparison, not unquestioned ground truth; that solver has known mesh-discretization bias against the published reference.
3. **Method effectiveness:** the existing P6 report compares CB-PFR against predeclared selection baselines using the three independent, high-budget P5 seeds for each of six layouts.

## Predeclared quantities and decision rules
- Canonical benchmark reference: (k_{eff}=1.18655), reported reference standard uncertainty (9.5\times10^{-5}); published maximum normalized pin power (2.498\pm0.16\%), minimum (0.232\pm0.58\%). See the C5G7 literature listed below.
- Internal project screening rule for canonical (k_{eff}): absolute difference no greater than 100 pcm **and** no greater than two combined standard uncertainties, with across-seed SEM combined in quadrature with the cited reference uncertainty. This is a project screen, **not an OECD/NEA acceptance limit**.
- Spatial comparison: preserve the 34×34 fuel-pin fission-rate shape derived from the 51×51 OpenMC mesh and compare it to the independently generated 34×34 normalized pin-power map. Report RMS relative error, mean absolute relative error, maximum absolute relative error, and the difference in peak/minimum normalized values. Since the OpenMC quantity is a fission-rate tally and the external solver calls its tally normalized pin power, this is a cross-code shape check, not an exact observable identity or a safety limit.
- CB-PFR effectiveness: use the existing P6 held-out regret analysis on P5, and honor the analyzer's integrity gates. A claimed advantage is limited to this six-layout model, declared proxy, and pilot. If the P6 interval includes zero, or integrity/convergence reviews remain open, report inconclusive evidence.

## Physical interpretation boundary
The six layouts are permutations of two UO2 and two MOX assemblies in the C5G7 2-D benchmark geometry, not six experimentally validated reactor designs. The canonical UMMU benchmark does not supply a design-specific (k_{eff}) acceptance band for the other five permutations. Thus this workflow cannot certify a candidate as safe, licensed, or comprehensively “physically better.” It can support a bounded statement about benchmark consistency and held-out relative fission-rate-shape ranking only.

The independent S_N solver uses a Cartesian digital-disk representation and reports a known resolution bias at its finest documented mesh (about −182 pcm in (k_{eff}), with peak normalized pin power below the Monte Carlo reference). Its computed output is retained as an independent numerical comparator with those limitations visible.

## Data provenance
- OECD/NEA C5G7 MOX benchmark: https://www.oecd-nea.org/jcms/pl_13548/benchmark-on-deterministic-transport-calculations-without-spatial-homogenisation
- Published MCNP/MOC results including (k_{eff}), pin-power extrema and distribution errors: https://www.frontiersin.org/journals/energy-research/articles/10.3389/fenrg.2020.00124/full
- Independent S_N solver (source pinned to commit `db421c969ee2de83e2d2ae2b14bda368567b558d`): https://github.com/EmreSakarya/c5g7-2d-transport-benchmark
- Source OpenMC campaign: https://github.com/thenextw4ng/cb-pfr/actions/runs/39098770358
