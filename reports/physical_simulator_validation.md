# Physical Simulator Validation Report

## Evidence classification

**Achieved:** software verification and independent extraction of the recorded production statepoint.  
**Withdrawn:** the earlier claim that the production scalar is benchmark-consistent. A critical audit found nonstandard log-spaced energy-group boundaries in the historical MGXS.  
**Not achieved:** standard-C5G7 benchmark verification, corrected high-budget candidate evaluation, or CB-PFR physical-hypothesis validation.

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

## Historical scalar comparison — withdrawn as benchmark evidence

The recorded production run reported k_eff = 1.1863941447 with standard deviation 5.6113e-05. An earlier comparison to the published value 1.18655 gave a difference near -15.6 pcm. **Do not interpret that agreement as benchmark validation.**

The historical MGXS was generated with np.logspace(-5, 7, 8), whereas the standard C5G7 seven-group boundaries are [1e-5, 0.0635, 10, 100, 1000, 500000, 1000000, 20000000] eV. The old production and smoke files can be byte-identical to each other while both encode the wrong group boundaries. The scalar difference and combined-uncertainty calculation are therefore withdrawn as a validation argument.

The corrected runner now substitutes the standard boundary list and checks the generated MGXS root group-structure attribute before transport. A new corrected high-budget run must be completed and the model reviewed against the primary specification before any reference comparison is reinstated.

### Reference-value correction

An earlier draft of this report listed approximately 1.16562 as a high-history reference and described a 12,000-history result near 1.16565 as compatible. That value is **not the standard 2-D C5G7 reference cited here**. Unless a separate model variant and source can be established, those values must not be used to validate the standard 2-D C5G7 case. Their provenance and model correspondence remain unresolved.

## Exploratory six-layout C5G7 smoke study

A separate 2×2 UO2/MOX assembly-placement formulation has now been run for all six layouts. The first smoke round completed six cases; a follow-up ran three explicit seed rounds (18 cases total) using 100 batches, 10 inactive batches, and 1,000 particles per batch. All 18 raw statepoints matched their recorded run manifests and OpenMC API-derived scalar results; 336/336 raw-HDF5 checks passed.

- [Six-layout smoke analysis](c5g7_smoke_run_2026-10-10.md)
- [Three-round repeatability analysis](c5g7_repeatability_smoke_2026-10-11.md)
- [Repeatability workflow and raw statepoint artifacts](https://github.com/thenextw4ng/cb-pfr/actions/runs/38097472734)

This is **historical exploratory smoke evidence only**, not standard-C5G7 benchmark validation. The reported k_eff ranking is descriptive rather than an optimization objective, and the budget is low. More importantly, these runs used the upstream log-spaced group boundaries, not the standard C5G7 boundaries. The prior one-ULP metadata observation was a separate serialization issue and did not detect the much larger group-structure mismatch. The corrected group audit is documented in the [input-provenance report](c5g7_input_provenance_comparison_2026-10-11.md).

## Production-versus-regenerated XML comparison

The [input-provenance comparison report](c5g7_input_provenance_comparison_2026-10-11.md) found exact equality for canonical geometry, tallies, and plots. The material XML definitions are identical after normalizing only the local `cross_sections` path. Settings differ by the expected compute budget and explicit smoke seed. Historical byte identity of the production and regenerated MGXS files only established that the same upstream data were reused; both had nonstandard log-spaced group boundaries. The prior endpoint-only patch was insufficient. The corrected runner now replaces the complete boundary list and checks the generated MGXS attribute before transport. Historical repeatability runs are pipeline evidence only, not standard C5G7 benchmark evidence. 

## Assembly-integrated fission-rate proxy smoke results

The [six-layout fission-rate proxy report](c5g7_assembly_fission_proxy_smoke_2026-10-11.md) and [CSV results](../results/c5g7_assembly_fission_proxy_smoke_2026-10-11.csv) now report assembly-integrated fission tally and a normalized peaking factor for all six layouts. This was one seed per layout at 100 batches / 10 inactive / 1,000 particles per batch. The metric is a fission-rate proxy, not absolute power; mesh-bin covariance is not propagated, and the ranking is not an optimization conclusion. These historical results used nonstandard log-spaced energy-group boundaries and must not be used for standard C5G7 physical ranking. The corrected runner now regenerates MGXS with the standard group boundaries.

## What remains unverified

1. The historical production statepoint's scalar/settings/tally metadata passed the OpenMC API audit, and the XML comparison confirms geometry/tally/plot equality plus material-definition equality after normalizing the local cross-section path. However, its MGXS uses nonstandard energy-group boundaries. A corrected standard-group transport rerun and boundary-condition/composition review against the primary specification are still required.
2. The historical production MGXS file is present and byte-identical to the old regenerated library, but both used nonstandard log-spaced group boundaries. The scalar match is withdrawn as benchmark evidence. Corrected standard-group runs and primary-specification review are required.
3. The archived run_01–run_03 stage34 outputs must be linked to exact candidate IDs and configuration/input hashes before they can support a candidate comparison.
4. The abstract QUBO categories (fresh, once_burned, twice_burned) still have no defensible mapping to C5G7 UO2/MOX material or depletion states.
5. Benchmark-grade candidate comparison still requires a reviewed physical model/material mapping, a predeclared objective and acceptance protocol, a higher common computational budget, and additional independent seeds per layout. The current three repeated runs per layout are smoke-budget only.

## Conclusion

The recorded production scalar and archived statepoint bytes have been independently audited, but the historical MGXS energy-group structure is nonstandard and the previous scalar-reference comparison is withdrawn. The corrected runner now enforces the standard seven-group boundary list, but corrected transport results and primary-specification review are still required. Historical six-layout smoke and repeatability results remain pipeline evidence only. No standard-C5G7 benchmark acceptance, benchmark-grade six-candidate evaluation, or physical CB-PFR validation is established.

## References

1. OECD Nuclear Energy Agency. *Benchmark on Deterministic Transport Calculations Without Spatial Homogenisation: MOX Fuel Assembly 3-D Extension Case*. OECD/NEA-hosted report, Table 1 reports the C5G7 first-stage Monte Carlo eigenvalue reference of 1.18655. https://www.oecd-nea.org/upload/docs/application/pdf/2019-12/nsc-doc2005-16.pdf
2. Frontiers in Energy Research. *GPU Based Two-Level CMFD Accelerating Two-Dimensional MOC Neutron Transport Calculation*. The 2-D C5G7 comparison table lists the reference k_eff = 1.18655 ± 9.5 pcm. https://www.frontiersin.org/journals/energy-research/articles/10.3389/fenrg.2020.00124/full
