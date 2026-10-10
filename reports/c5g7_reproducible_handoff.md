# Reproducible C5G7 reference handoff (independent of CB-PFR candidate validation)

## Purpose and boundary

This handoff makes the selected public C5G7 transport benchmark implementation discoverable and reproducible as a **separate transport-code exercise**. It does not map CB-PFR's abstract `fresh`, `once_burned`, or `twice_burned` states to UO2/MOX, and it does not by itself validate CB-PFR candidate rankings.

The upstream source is the MIT Computational Reactor Physics Group's public benchmark collection:
- Repository: https://github.com/mit-crpg/benchmarks
- C5G7 OpenMC model directory: https://github.com/mit-crpg/benchmarks/tree/master/c5g7/openmc
- Upstream runner lists the pin, 2-D, 3-D, unrodded, rodded-A, and rodded-B exercises: https://github.com/mit-crpg/benchmarks/blob/master/c5g7/openmc/run_all.sh
- Benchmark specification: OECD/NEA, *Benchmark specification for deterministic 2-D/3-D MOX fuel assembly transport calculations without spatial homogenization*: https://www.oecd-nea.org/jcms/pl_13548/benchmark-on-deterministic-transport-calculations-without-spatial-homogenisation

The upstream model is an implementation reference. Before claiming a benchmark reproduction, select one exact exercise and compare its geometry, materials, boundary conditions, nuclear data, tally definitions, and reference values against the applicable primary benchmark specification.

## Prepare source and preserve provenance

Run from the repository root in an environment where Git is installed:

```bash
mkdir -p external\npython scripts/prepare_c5g7_reference.py --destination external/mit-crpg-benchmarks
```

The script clones the public upstream repository into a new destination and writes `UPSTREAM_PROVENANCE.json` containing the full checked-out commit SHA, source URL, and UTC preparation time. It refuses to overwrite an existing destination. Preserve that provenance file with all subsequent outputs.

This step downloads source code only. It does not install OpenMC, download nuclear data, execute a transport calculation, or certify any reference result.

## Environment and run protocol

1. Create a clean environment following the upstream repository's current setup requirements and the selected OpenMC version's installation guide: https://docs.openmc.org/en/stable/quickinstall.html
2. Inspect `external/mit-crpg-benchmarks/c5g7/openmc/run_all.sh` and the selected case's `build-xml-*.py` before running anything. Select a single case explicitly; do not run all cases by default.
3. Record Python/OpenMC versions, OS, CPU, exact upstream commit SHA, command line, random seed, particles, batches, inactive batches, runtime, and all input/output hashes.
4. Run the selected upstream case from its own directory, preserving stdout and stderr. The upstream `run_all.sh` runs multiple cases sequentially; use it only if that full workload is intended.
5. Before inspecting results, predeclare the benchmark quantity, reference source, comparison metric, statistical treatment, and acceptance tolerance.
6. Compare only like-for-like quantities. Report Monte Carlo statistical uncertainty and benchmark/reference uncertainty where available.
7. Archive raw outputs and a machine-readable run manifest. If the baseline does not meet the predeclared criterion, stop and investigate before any candidate analysis.

## What this enables—and what remains blocked

**Enabled:** a traceable way to obtain the public C5G7 implementation source and identify the exact source revision used for a future independent transport benchmark run.

**Still required for C5G7 baseline verification:** a selected case, reviewed specification transcription, compatible data, a successful run, and a comparison to primary reference values.

**Still required for CB-PFR physical validation:** a scientifically justified reformulation or documented mapping from every optimizer candidate to model geometry and physical compositions/depletion states. The current abstract QUBO does not provide that mapping. Do not treat a successful standalone C5G7 run as validation of the current QUBO candidates.

## Sources

- OECD Nuclear Energy Agency, C5G7 benchmark page and specification (above).
- MIT CRPG, public reactor-physics benchmark collection (above).
- OpenMC, installation documentation: https://docs.openmc.org/en/stable/quickinstall.html
