# C5G7 model audit

## Primary sources

1. OECD/NEA, [Benchmark on Deterministic Transport Calculations Without Spatial Homogenisation](https://www.oecd-nea.org/jcms/pl_13548/benchmark-on-deterministic-transport-calculations-without-spatial-homogenisation); see also the [3-D extension specification and reference results](https://www.oecd-nea.org/upload/docs/application/pdf/2019-12/nsc-doc2005-16.pdf).
2. MIT Computational Reactor Physics Group, [benchmark model repository](https://github.com/mit-crpg/benchmarks), specifically the pinned source revision `ba41bee54320ada0b4ac39a0dd2ca3c1d090a450` used by the quick-check.
3. OpenMC, [statepoint file format](https://docs.openmc.org/en/stable/io_formats/statepoint.html) and [tally methods/statistics](https://github.com/openmc-dev/openmc/blob/develop/docs/source/methods/tallies.rst).
4. Song et al. (2020), [GPU Based Two-Level CMFD Accelerating Two-Dimensional MOC Neutron Transport Calculation](https://doi.org/10.3389/fenrg.2020.00124), Table 1.

## Run identity and configuration evidence

The GitHub Actions quick-check used OpenMC 0.16.0, the MIT-CRPG source revision above, the 2-D 2x2 UO2/MOX arrangement with signature `UMMU`, a 51x51 fission mesh, 20 batches, 5 inactive batches, 100 particles per batch, one thread, and seed base 811011. The uploaded artifact contains the generated model builder, geometry/material/settings/tally XML, MGXS HDF5, OpenMC log, statepoint, summary, run manifest, and fission analysis.

The run is an actual transport calculation; the HDF5 audit passing verifies statepoint structure and expected metadata. It does not prove every benchmark input agrees with the primary specification.

## Critical model-identity gate

The project manifest itself records that the older upstream model builder used `np.logspace(-5, 7, 8)`, which is not the official C5G7 seven-group energy structure. The quick-check runner replaces this expression with the C5G7 boundaries:

`[1e-5, 0.0635, 10, 100, 1000, 500000, 1000000, 20000000] eV`

and checks the generated MGXS root group-structure attribute. This correction is necessary, but is not a complete review of every benchmark dimension, composition, density, temperature, boundary condition, and tally definition. An independent reviewer must diff generated inputs against the primary benchmark specification and record hashes before G0 can pass.

## Numerical results from the quick-check

- (k_{eff}=1.1728029349321403)
- Reported OpenMC within-run standard deviation: (0.019472323678449033)
- Assembly-integrated fission-rate peaking factor: (1.942932842839654)
- Total batches: 20; inactive batches: 5; active batches: 15; nominal particles per batch: 100.
- Raw statepoint audit: 22 checks passed, 0 failed.

The standard deviation is large compared with the published reference uncertainty; this run is underpowered for acceptance. The difference in (k_{eff}) is a screening calculation only and must not be interpreted as benchmark failure or pass. No arbitrary acceptance criterion is applied.

## Observable definitions

The local metric is:

[
F_{assembly}=rac{max_a R_a}{operatorname{mean}_a R_a},
]

where (R_a) is the sum of fission-score mesh means in each 17x17 fuel-assembly block. This is a dimensionless *assembly-integrated fission-rate peaking proxy*. It is not absolute power and is not the same observable as the publication's maximum normalized pin power of 2.498. Those values must not be subtracted or ratio-compared.

## Status

**Execution:** PASS. **Raw statepoint audit:** PASS. **Model identity:** BLOCKED pending primary-specification review. **Benchmark convergence/acceptance:** NOT ESTABLISHED. **Physical experiment validation:** NOT ESTABLISHED.


## Follow-up three-seed execution evidence

The independent workflow [38112597526](https://github.com/thenextw4ng/cb-pfr/actions/runs/38112597526) completed 18 corrected-group runs: six layout signatures and three independent seeds per layout, all with common settings (100 batches, 10 inactive, 1,000 particles per batch). All 18 group-structure audits passed, all statepoint hashes were unique, and the raw-HDF5 spatial-mapping audit passed for all 18 cases. The shared MGXS hash was `a4328a7b012321fbe8f661745aa135f0a2eecd34cf475429e160865204acb129`.

For UMMU, mean (k_{eff}=1.1861026314), between-seed SD (0.0038633985); mean assembly fission peaking (1.8861131573), between-seed SD (0.0289951863). This remains a low-budget smoke study; no layout winner is declared and benchmark acceptance is blocked pending full model-identity review and a justified convergence protocol.
