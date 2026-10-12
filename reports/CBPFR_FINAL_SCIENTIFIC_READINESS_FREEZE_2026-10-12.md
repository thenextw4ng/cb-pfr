# CB-PFR Final Scientific Readiness Freeze — A–G
**Decision date:** 2026-10-12  
**Scope:** CB-PFR / ReactorQ Studio C5G7 four-fuel-position placement study  
**Status:** ACCEPTANCE CONTRACT FROZEN; PHYSICAL VALIDATION NOT YET PASSED

## Canonical acceptance contract

The authoritative A–G goal is now explicitly scientific and physical validation, not software readiness alone:

[CB-PFR Scientific and Physical Validation Contract — A–G](https://github.com/thenextw4ng/cb-pfr/blob/main/reports/CBPFR_SCIENTIFIC_PHYSICAL_VALIDATION_CONTRACT_A-G_2026-10-12.md)

That contract defines the evidence and pass criteria for each gate:
- **A:** model fidelity to the primary C5G7 specification and exact-run provenance.
- **B:** physically correct geometry/tally mapping and compatible spatial-reference comparison.
- **C:** exact QUBO/design-space mapping plus a predeclared, uncertainty-aware physical selection rule.
- **D:** intact reproducible runs, intended independence, and adequate source/eigenvalue convergence evidence.
- **E:** uncertainty-aware comparison with compatible trusted benchmark quantities under justified criteria.
- **F:** fail-closed scientific evidence pipeline; software CI cannot confer physical-validation status.
- **G:** final synthesis, bounded scientific claims, reproducible release, and evidence traceability.

## Frozen scope and study identity

The study enumerates six layouts across four fuel positions with exactly two UO₂ and two MOX assemblies; five reflector positions remain fixed. It is a C5G7 assembly-placement reformulation, not a direct reproduction of the legacy Usmanov burnup-state QUBO.

Do not add new algorithms, metrics, experiments, or cosmetic refactors except to close a documented scientific-validity blocker, reproducible defect, failing test, or explicit submission requirement. Do not change the active canonical model/settings without versioning the change and recording input hashes.

No QPU execution, quantum advantage, reactor-safety certification, absolute-power-in-watts claim, or validation of unmeasured quantities is implied.

## Current scientific status

Evidence exists for three high-budget canonical UMMU runs, raw HDF5 audits, artifact integrity, provisional scalar comparison, and a normalized spatial-distribution comparison. These results do **not** establish complete physical validation.

The principal blockers are:
1. Independent review of fidelity to the primary benchmark specification and physics-significant model/group/source differences.
2. Source/eigenvalue stationarity is not certified; recovered trace shifts remain subject to qualified review or a predeclared, justified follow-up protocol.
3. Six-layout results are screening-budget data, while only UMMU has the current high-budget confirmation. A physical winner cannot be claimed without an approved objective/acceptance rule and adequate comparable evidence.
4. Spatial claims remain limited to the normalized distribution comparison actually supported; no absolute power or flux claim.
5. The workflow repair must be reviewed and merged through the normal repository process, then the final release commit and evidence outputs must be verified.

## Definition of done

The project is complete only when:
1. The applicable A–F criteria in the canonical contract have passed with traceable evidence and documented review; and
2. G confirms that manuscript, software, figures, data, and conclusions agree with that evidence; and
3. every physical-validation claim is bounded to the configurations and quantities actually validated.

A successful test suite, completed OpenMC run, close scalar benchmark value, or normalized spatial agreement alone is not sufficient. If convergence or model fidelity remains unresolved, report the result as numerically screened / validation-inconclusive, not physically validated.

## Stop rule

Do not run more expensive transport simply to obtain a preferred result. Before any follow-up transport, document the unresolved scientific question, the protocol and acceptance criterion, the settings to be changed (if any), and why the current evidence cannot answer it. Preserve existing results and report negative or inconclusive findings honestly.
