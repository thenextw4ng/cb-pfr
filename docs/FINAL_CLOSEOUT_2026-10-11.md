# ReactorQ Studio — bounded closeout (2026-10-11)

## Decision

The research-prototype milestone is evidence-frozen. Existing software and transport evidence is packaged; do not extend this milestone indefinitely just because physical-validation evidence is unavailable.

Release description: **research prototype with synthetic CB-PFR results and exploratory OpenMC C5G7 transport evidence**. Do not describe this as experimentally validated, benchmark-accepted, reactor-safe, or as a validated burnup-state QUBO-to-C5G7 workflow.

## Evidence actually run

- Abstract four-bit QUBO: exhaustive enumeration of all 16 bit strings; six satisfy the exact-two constraint.
- OpenMC 0.16.0 quick-check ran a new transport case; raw statepoint audit passed 22/22 checks: https://github.com/thenextw4ng/cb-pfr/actions/runs/38112118549
- An 18-case study ran six layouts with three seeds each, 100 batches, 10 inactive batches, 1,000 particles/batch, one thread. Group structure, unique statepoint hashes, common MGXS hash, and spatial mapping audits passed: https://github.com/thenextw4ng/cb-pfr/actions/runs/38112597526
- CI passed 157 tests on each of Python 3.10, 3.11, and 3.12 at commit `3f584305fc5101b272b7dc546bcc9429ef025c80`: https://github.com/thenextw4ng/cb-pfr/actions/runs/38112944829

## Numerical screen

Reference: Song et al. (2020), Table 1, https://doi.org/10.3389/fenrg.2020.00124; reported (k_{eff}=1.18655\pm0.000095) and maximum normalized pin power 2.498.

For UMMU, three seed runs gave mean (k_{eff}=1.1861026314460645), between-seed SD (0.0038633985032438967), and standard error of the mean (0.0022305341658346613). Difference from the reference: (-0.0004473685539359007), or (-0.0377033\%). This is a low-budget numerical screen, not benchmark acceptance; model identity, convergence, and an agreed acceptance criterion are not established.

Mean assembly-integrated fission-rate peaking was 1.8861131573187928 (between-seed SD 0.028995186254547157; SE 0.01674037858926614). It is **not comparable** to the reference's maximum normalized pin power of 2.498. No error between those metrics is reported.

## Final status

| Requirement | Status | Meaning |
|---|---|---|
| Abstract QUBO and exact-two constraint | PASS | Software-level combinatorial verification |
| Python CI | PASS | 157 tests on each supported Python version |
| OpenMC transport smoke execution | PASS | Execution only |
| Raw statepoint technical audit | PASS | Audit scope only |
| Six-layout/three-seed repeatability smoke | PASS | Descriptive evidence |
| (k_{eff}) numerical comparison | PASS | Difference recorded, not acceptance |
| Benchmark reproduced/accepted | BLOCKED | Model identity, convergence, acceptance criteria unestablished |
| Assembly peaking compared with pin-power reference | BLOCKED | Different observables |
| Legacy burnup QUBO mapped to C5G7 material | BLOCKED | No defensible mapping found |
| Experimental physical validation | BLOCKED | No comparable experimental dataset and uncertainty budget |
| Research UI prototype | PASS | Can display evidence with status labels |
| Production UI for validated physical recommendations | BLOCKED | Scientific validation and production lifecycle not established |

## Evidence

- [Repeatability summary](../results/c5g7_repeatability_reexecution_2026-10-11.json)
- [Numerical comparison CSV](../results/benchmark_comparison.csv)
- [Validation evidence matrix](VALIDATION_EVIDENCE.md)
- [C5G7 model audit](C5G7_MODEL_AUDIT.md)
- [Independent validation notes](INDEPENDENT_VALIDATION.md)
- [API contract](api.md)

## Closeout rule

No further software changes are required to describe this bounded research-prototype milestone. Physical validation is a separate evidence task, not a missing CI checkbox. Any later physical claim requires genuinely comparable data and an independently reviewed model mapping. Preserve all prior results and provenance.
