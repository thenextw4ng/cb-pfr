# Physical Simulator Validation Report

## Evidence classification

**Achieved:** software verification plus a recorded C5G7/OpenMC execution baseline.  
**Limited scalar comparison:** the recorded production baseline is numerically close to the published 2-D C5G7 reference.  
**Not achieved:** complete benchmark verification, benchmark-grade candidate evaluation, or CB-PFR physical-hypothesis validation.

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

## Exploratory six-layout C5G7 smoke study

A separate 2×2 UO2/MOX assembly-placement formulation has now been run for all six layouts. The first smoke round completed six cases; a follow-up ran three explicit seed rounds (18 cases total) using 100 batches, 10 inactive batches, and 1,000 particles per batch. All 18 raw statepoints matched their recorded run manifests and OpenMC API-derived scalar results; 336/336 raw-HDF5 checks passed.

- [Six-layout smoke analysis](c5g7_smoke_run_2026-10-10.md)
- [Three-round repeatability analysis](c5g7_repeatability_smoke_2026-10-11.md)
- [Repeatability workflow and raw statepoint artifacts](https://github.com/thenextw4ng/cb-pfr/actions/runs/38097472734)

This is **exploratory smoke-budget evidence**, not benchmark-grade validation. The reported k_eff ranking is descriptive rather than an optimization objective; the current budget is low, only three repetitions exist per layout, and exact production-vs-smoke materials metadata correspondence remains under review. The repeated-run analysis found one root MGXS metadata energy boundary differing by one floating-point step across separate workflow invocations, while all 63 dataset payloads matched; see the [machine-readable comparison](../results/c5g7_repeatability_smoke_2026-10-11/mgxs_semantic_comparison.json).

## Production-versus-regenerated XML comparison

The [input-provenance comparison report](c5g7_input_provenance_comparison_2026-10-11.md) found exact equality for canonical geometry, tallies, and plots. The material XML definitions are identical after normalizing only the local `cross_sections` path. Settings differ by the expected compute budget and explicit smoke seed. The production `mgxs.h5` and regenerated canonical library are byte-identical: SHA-256 `170cc799f496e952465583bb078b2a88eae0f09886a821fd7ee8999d1eb93216`; all 63 datasets and all metadata match. See the [direct MGXS comparison workflow](https://github.com/thenextw4ng/cb-pfr/actions/runs/38100560219). An earlier repeatability artifact had a different MGXS hash with a one-ULP root energy-boundary difference. The source uses `np.logspace(-5, 7, 8)` when generating the group structure; the preparation adapter now normalizes the endpoints explicitly. The normalized 18-run repeatability workflow now confirms all runs share the production-identical MGXS hash; see [normalized repeatability evidence](../results/c5g7_repeatability_normalized_2026-10-11/README.md). The primary-specification review remains open.

## Assembly-integrated fission-rate proxy smoke results

The [six-layout fission-rate proxy report](c5g7_assembly_fission_proxy_smoke_2026-10-11.md) and [CSV results](../results/c5g7_assembly_fission_proxy_smoke_2026-10-11.csv) now report assembly-integrated fission tally and a normalized peaking factor for all six layouts. This was one seed per layout at 100 batches / 10 inactive / 1,000 particles per batch. The metric is a fission-rate proxy, not absolute power; mesh-bin covariance is not propagated, and the ranking is not an optimization conclusion. The workflow used the MGXS file byte-identical to the production library.

## What remains unverified

1. The production statepoint's scalar/settings/tally metadata have passed the OpenMC API audit and a separate raw-HDF5 comparison. The XML comparison now confirms geometry/tally/plot equality and material-definition equality after normalizing the local cross-section path. Remaining benchmark verification includes explaining the cross-workflow MGXS discrepancy and completing boundary-condition/composition review against the primary specification.
2. The production MGXS file is present and byte-identical to the regenerated canonical library. Exact correspondence to the primary benchmark specification and the official comparison protocol still need review before interpreting the scalar match as benchmark verification.
3. The archived run_01–run_03 stage34 outputs must be linked to exact candidate IDs and configuration/input hashes before they can support a candidate comparison.
4. The abstract QUBO categories (fresh, once_burned, twice_burned) still have no defensible mapping to C5G7 UO2/MOX material or depletion states.
5. Benchmark-grade candidate comparison still requires a reviewed physical model/material mapping, a predeclared objective and acceptance protocol, a higher common computational budget, and additional independent seeds per layout. The current three repeated runs per layout are smoke-budget only.

## Conclusion

The recorded production scalar is consistent in scale with the published 2-D C5G7 reference, and its extraction has now been independently cross-checked from the committed HDF5 bytes. Exact model/nuclear-data correspondence and full benchmark acceptance remain unverified. Six layouts have exploratory smoke results, three-seed repeatability data at low budget, and one-seed assembly fission-rate proxy outputs. No benchmark-grade six-candidate evaluation or physical CB-PFR validation is established.

## References

1. OECD Nuclear Energy Agency. *Benchmark on Deterministic Transport Calculations Without Spatial Homogenisation: MOX Fuel Assembly 3-D Extension Case*. OECD/NEA-hosted report, Table 1 reports the C5G7 first-stage Monte Carlo eigenvalue reference of 1.18655. https://www.oecd-nea.org/upload/docs/application/pdf/2019-12/nsc-doc2005-16.pdf
2. Frontiers in Energy Research. *GPU Based Two-Level CMFD Accelerating Two-Dimensional MOC Neutron Transport Calculation*. The 2-D C5G7 comparison table lists the reference k_eff = 1.18655 ± 9.5 pcm. https://www.frontiersin.org/journals/energy-research/articles/10.3389/fenrg.2020.00124/full
