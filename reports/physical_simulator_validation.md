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

**Provenance status:** these values were initially transcribed from the researcher's terminal output, then independently read through OpenMC 0.16.0; the API-derived mean and standard deviation matched the recorded summary. A separate raw-HDF5 audit of the committed ZIP also passed 10/10 checks across Python 3.10, 3.11, and 3.12. The audited statepoint member is `c5g7-run/2d/statepoint.20000.h5`, SHA-256 `0d76dc1a14a2b74a388c01883f01e5c3095480d53eee885910ca2a0c57e6b882`. This verifies extraction and consistency of the recorded metadata, not the correctness of geometry, nuclear data, or benchmark correspondence.

## Scalar comparison with the standard 2-D C5G7 reference

Using k_ref = 1.18655, the recorded baseline differs by:

- Absolute difference: -0.0001558553
- Difference in pcm: approximately -15.6 pcm
- Relative difference: approximately -0.0131%

A published reference uncertainty of approximately 9.5 pcm is reported in a later C5G7 benchmark comparison [2]. Combining that uncertainty with the recorded baseline's reported standard deviation gives an approximate combined standard uncertainty of 11.0 pcm; the difference is about 1.4 combined standard deviations. This is a **limited scalar consistency check**, conditional on the production model, nuclear data, and benchmark variant matching the reference assumptions. It is not sufficient to claim full benchmark validation.

### Reference-value correction

An earlier draft of this report listed approximately 1.16562 as a high-history reference and described a 12,000-history result near 1.16565 as compatible. That value is **not the standard 2-D C5G7 reference cited here**. Unless a separate model variant and source can be established, those values must not be used to validate the standard 2-D C5G7 case. Their provenance and model correspondence remain unresolved.

## What remains unverified

1. The production statepoint's scalar/settings/tally metadata have passed the OpenMC API audit and a separate raw-HDF5 comparison. The remaining benchmark-verification task is to compare exact geometry, boundary conditions, material definitions, MGXS source and hashes with the primary benchmark specification.
2. The model/data correspondence and benchmark acceptance tolerance must be reviewed before interpreting the scalar match as benchmark verification.
3. The archived run_01–run_03 stage34 outputs must be linked to exact candidate IDs and configuration/input hashes before they can support a candidate comparison.
4. The abstract QUBO categories (fresh, once_burned, twice_burned) still have no defensible mapping to C5G7 UO2/MOX material or depletion states.
5. Candidate-level comparisons require a reviewed physical mapping, a predeclared common computational budget, repeated runs where appropriate, and uncertainty analysis for both Monte Carlo noise and between-run variation.

## Conclusion

The recorded production scalar is consistent in scale with the published 2-D C5G7 reference, and its extraction has now been independently cross-checked from the committed HDF5 bytes. Exact model/nuclear-data correspondence and full benchmark acceptance remain unverified. No six-candidate physical comparison or physical CB-PFR validation is established.

## References

1. OECD Nuclear Energy Agency. *Benchmark on Deterministic Transport Calculations Without Spatial Homogenisation: MOX Fuel Assembly 3-D Extension Case*. OECD/NEA-hosted report, Table 1 reports the C5G7 first-stage Monte Carlo eigenvalue reference of 1.18655. https://www.oecd-nea.org/upload/docs/application/pdf/2019-12/nsc-doc2005-16.pdf
2. Frontiers in Energy Research. *GPU Based Two-Level CMFD Accelerating Two-Dimensional MOC Neutron Transport Calculation*. The 2-D C5G7 comparison table lists the reference k_eff = 1.18655 ± 9.5 pcm. https://www.frontiersin.org/journals/energy-research/articles/10.3389/fenrg.2020.00124/full
