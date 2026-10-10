# Benchmark selection and physical-mapping decision

**Decision:** use the OECD/NEA C5G7 MOX fuel-assembly transport benchmark as a *reference framework for future transport-code verification*, not as an automatic physical interpretation of the current QUBO states.

## Why C5G7 is a defensible reference family

The OECD/NEA describes C5G7 as a benchmark for deterministic neutron-transport calculations without spatial homogenisation. Its model family includes UO2 and multiple MOX enrichment regions and defines 2-D and 3-D exercises. The benchmark specification and its reference-result appendices are the authoritative sources for the exact exercise, compositions, geometry, boundary conditions, tallies, and comparison values. See the primary sources below.

- OECD Nuclear Energy Agency, [Benchmark on Deterministic Transport Calculations Without Spatial Homogenisation](https://www.oecd-nea.org/jcms/pl_13548/benchmark-on-deterministic-transport-calculations-without-spatial-homogenisation).
- OECD/NEA, [MOX Fuel Assembly 3-D Extension Case specification and reference analysis (NSC DOC 2005-16)](https://www.oecd-nea.org/upload/docs/application/pdf/2019-12/nsc-doc2005-16.pdf).
- OpenMC project, [examples and C5G7 implementation notes](https://docs.openmc.org/en/stable/_modules/openmc/examples.html). These notes can help with implementation but do not supersede the benchmark specification.

C5G7 is a transport benchmark, not a burnup-management dataset. UO2 and MOX enrichment labels do not encode the states `fresh`, `once_burned`, and `twice_burned`. A benchmark's existence therefore does not supply the missing map from this repository's abstract candidate vectors to physical fuel configurations.

## Chosen benchmark role and excluded claims

The machine-readable record at `config/benchmarks/c5g7_manifest.json` selects the C5G7 source family for reference-problem definition. It deliberately records the implementation as **not instantiated**: no complete OpenMC model, compatible cross-section package, transcribed reference values, validated baseline run, or defensible candidate map is bundled by this change.

Do not claim that:
- the seven-position QUBO is a C5G7 core or assembly;
- the three abstract burnup categories correspond to UO2/MOX enrichment classes;
- the OpenMC model is built, the baseline converged, or the benchmark was reproduced;
- any `k_eff`, flux, or power value was obtained by CB-PFR;
- selecting C5G7 alone validates the physical interpretation of the optimizer.

## Required mapping contract

Before physical candidate evaluation can be enabled, an implementation must provide and independently review all of the following:

1. **Position map:** each QUBO position maps to a precisely identified pin, assembly, or region in the selected benchmark exercise, with a documented geometry transformation.
2. **State-to-material map:** every QUBO state maps to an explicit material/composition or a documented depletion state at a defined burnup and cooling condition. A label alone is not evidence.
3. **Composition provenance:** isotope number densities or atom/mass fractions, densities, temperatures, and source table/section are recorded without silently substituting compositions.
4. **Nuclear-data provenance:** library identity/version, source, temperature coverage, file/index integrity, and checksum where available.
5. **Model specification:** exact 2-D/3-D case, geometry, boundary conditions, settings, tally definitions, and normalization convention are recorded.
6. **Reference protocol:** published reference quantity, comparison metric, acceptance tolerance, uncertainty treatment, and convergence criteria are set before looking at candidate results.
7. **Reproducibility:** immutable inputs, OpenMC version, random seed, run status, stdout/stderr, statepoint, tallies, and checksums are preserved.

If any required item is missing, the candidate-to-physics path remains blocked.

## Automated gate

Audit the manifest with:

```bash
python scripts/audit_benchmark_manifest.py \
  --input config/benchmarks/c5g7_manifest.json \
  --output results/c5g7_benchmark_gate.json
```

The current manifest is expected to return exit code `2` and status `blocked`. That is the correct fail-closed outcome: the benchmark selection and source dossier are documented, but the missing model and mapping evidence have not been fabricated. The tool checks manifest structure and declared gates; it does not fetch or independently authenticate source documents and does not validate reactor physics.

## Status

**Benchmark family selected; model/mapping gate remains blocked.** Phase 3 can establish a defensible benchmark specification and enforce the required mapping contract in software, but physical CB-PFR validation cannot honestly be marked complete until the actual model, material/depletion mapping, and baseline evidence exist.
