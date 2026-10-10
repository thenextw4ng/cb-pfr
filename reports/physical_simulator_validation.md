# Physical Simulator Validation Report

## Evidence classification

**Achieved:** software verification plus a recorded C5G7/OpenMC execution baseline.  
**Limited scalar comparison:** the recorded production baseline is numerically close to the published 2-D C5G7 reference.  
**Not achieved:** complete benchmark verification, candidate-level physical comparison, or CB-PFR physical-hypothesis validation.

The executed model is identified in the local manifest as a 2-D, seven-group C5G7 eigenvalue run. The official benchmark literature reports a reference eigenvalue of approximately 1.18655 for the 2-D C5G7 problem; see the OECD/NEA-hosted benchmark report and the later summary of the reference result [1, 2].

## Recorded production baseline

| Quantity | Recorded value |
|---|---:|
| OpenMC version | 0.16.0 |
| Run mode | eigenvalue |
| Energy mode | multi-group |
| Batches | 20,000 |
| Inactive batches | 500 |
| Particles per batch | 10,000 |
| Reported realizations | 19,500 |
| Recorded k_eff | 1.1863941447 |
| Reported standard deviation | 0.0000561134 |
| Mesh tally dimension | 51 × 51 × 1 |
| Mesh tally scores | flux, fission, nu-fission |

**Provenance limitation:** these values were transcribed from the researcher's terminal output. The raw evidence ZIP is committed to the evidence branch and its ZIP integrity/statepoint-file presence pass CI, but the HDF5 values have not yet been independently recomputed in the current integration environment. Treat this table as a recorded baseline until the statepoint audit and semantic cross-check are run.

## Scalar comparison with the standard 2-D C5G7 reference

Using k_ref = 1.18655, the recorded baseline differs by:

- Absolute difference: -0.0001558553
- Difference in pcm: approximately -15.6 pcm
- Relative difference: approximately -0.0131%

A published reference uncertainty of approximately 9.5 pcm is reported in a later C5G7 benchmark comparison [2]. Combining that uncertainty with the recorded baseline's reported standard deviation gives an approximate combined standard uncertainty of 11.0 pcm; the difference is about 1.4 combined standard deviations. This is a **limited scalar consistency check**, conditional on the production model, nuclear data, and benchmark variant matching the reference assumptions. It is not sufficient to claim full benchmark validation.

### Reference-value correction

An earlier draft of this report listed approximately 1.16562 as a high-history reference and described a 12,000-history result near 1.16565 as compatible. That value is **not the standard 2-D C5G7 reference cited here**. Unless a separate model variant and source can be established, those values must not be used to validate the standard 2-D C5G7 case. Their provenance and model correspondence remain unresolved.

## What remains unverified

1. The raw statepoint.20000.h5 must be read using the OpenMC API and compared with the transcribed values using scripts/audit_openmc_statepoint.py and scripts/compare_openmc_baseline.py.
2. The exact geometry, boundary conditions, material definitions, MGXS source and hashes must be compared with the benchmark specification.
3. The archived run_01–run_03 stage34 outputs must be linked to exact candidate IDs and configuration/input hashes before they can support a candidate comparison.
4. The abstract QUBO categories (fresh, once_burned, twice_burned) still have no defensible mapping to C5G7 UO2/MOX material or depletion states.
5. Candidate-level comparisons require a reviewed physical mapping, a predeclared common computational budget, repeated runs where appropriate, and uncertainty analysis for both Monte Carlo noise and between-run variation.

## Conclusion

The recorded production scalar is consistent in scale with the published 2-D C5G7 reference, but its HDF5 values still require independent recomputation and the exact model/nuclear-data correspondence must be checked. No six-candidate physical comparison or physical CB-PFR validation is established.

## References

1. OECD Nuclear Energy Agency. *Benchmark on Deterministic Transport Calculations Without Spatial Homogenisation: MOX Fuel Assembly 3-D Extension Case*. OECD/NEA-hosted report, Table 1 reports the C5G7 first-stage Monte Carlo eigenvalue reference of 1.18655. https://www.oecd-nea.org/upload/docs/application/pdf/2019-12/nsc-doc2005-16.pdf
2. Frontiers in Energy Research. *GPU Based Two-Level CMFD Accelerating Two-Dimensional MOC Neutron Transport Calculation*. The 2-D C5G7 comparison table lists the reference k_eff = 1.18655 ± 9.5 pcm. https://www.frontiersin.org/journals/energy-research/articles/10.3389/fenrg.2020.00124/full
