# Stage 6 — Scientific evidence matrix and closure plan (2026-10-11)

## Decision

**Stage 6 is not closed.** Public benchmark references can establish the provenance of a reference C5G7 model and its seven-group data, but they do not, by themselves, prove that the project's legacy QUBO states fresh, once_burned, and twice_burned correspond to specific C5G7 materials. The defensible path is to separate (A) a clearly defined UO2/MOX layout demonstration from (B) any burnup/depletion interpretation.

## Primary reference sources

1. **Lewis et al., C5G7 benchmark specification** — *Benchmark specification for Deterministic 2-D/3-D MOX Fuel Assembly Transport Calculations Without Spatial Homogenization*, NEA/NSC/DOC(2001)4. An OECD/NEA-hosted benchmark-specification PDF is available at:
   https://harbor.oecd-nea.org/upload/docs/application/pdf/2020-01/nsc-wpfc-doc2012-16.pdf
   Use this as the primary reference for benchmark scope, material definitions, assembly geometry, and reference problem specification. Verify the exact document revision and relevant tables before transcribing numerical inputs.

2. **OpenMC multigroup C5G7 example** — OpenMC documentation demonstrates constructing the 2-D C5G7 problem and states that data are taken from Appendix A of the benchmark specification:
   https://docs.openmc.org/en/v0.12.2/examples/mg-mode-part-i.html
   This is an implementation example, not a substitute for the benchmark specification.

3. **OpenMC stable data configuration documentation** — explains how continuous-energy and multigroup nuclear data are configured and located:
   https://docs.openmc.org/en/stable/usersguide/data.html
   Record the actual MGXS file hash, its origin, group structure, temperature and correction conventions. A file hash establishes identity, not correctness.

4. **OECD/NEA C5G7-TD benchmark overview** — describes C5G7 as a transport-code benchmark based on a mini-core with UO2 and MOX assemblies:
   https://oecd-nea.org/science/wprs/egrts/c5g7-td/
   Use this for context only; use the applicable steady-state specification for numerical acceptance values.

5. **OECD/NEA PWR MOX/UO2 transient benchmark** — a separate benchmark with its own core definition and specifications:
   https://www.oecd-nea.org/jcms/pl_46518/nea-and-us-nrc-pwr-mox-uo2-core-transient-benchmark-final-specifications-2003
   Do not mix its compositions, geometry, or acceptance criteria into C5G7 without a justified model conversion.

## Evidence matrix

| Claim / requirement | Evidence to collect | Current status | Closure rule |
|---|---|---|---|
| Seven-group boundaries are correct | Exact group-edge array in generated input and MGXS metadata | Re-audited in both completed high-budget statepoints and 18-case corrected smoke artifact; shared MGXS hash is recorded. Benchmark-table correctness still needs review | Preserve the raw metadata and compare material/nuclear-data provenance with the applicable primary specification |
| Nuclear data provenance is traceable | Upstream source/revision, generation procedure, file hash, group edges, temperature and correction conventions | Some workflow provenance exists; benchmark-level correctness still requires review | Independent reviewer compares generated library to benchmark source tables |
| Geometry and material regions match intended model | Generated geometry/lattice files, candidate manifest, raw statepoint tally-support audit | Structural position and mesh-to-assembly mapping passed for 18 smoke cases; two high-budget UMMU statepoints also passed raw-HDF5 audits. Not physical validation | Compare material compositions and all benchmark-specific dimensions/boundaries with the primary specification |
| Four-position QUBO means exactly two MOX and two UO2 | QUBO matrix/constraints, exhaustive enumeration of all 16 bitstrings, six feasible layouts | Constraint is combinatorial, not a physical claim | Automated test must show exactly six feasible assignments and mapping of each bit to a documented location |
| Each QUBO state maps to a material | Versioned mapping table with semantic definition and source for each state | Legacy fresh/once_burned/twice_burned mapping is not defensible from current evidence | Do not map burnup labels to UO2/MOX by assumption; provide isotope/depletion data or declare a new, separate UO2/MOX formulation |
| Burned states represent actual depletion | Initial isotopics, irradiation history, power/flux history, depletion-chain provenance, cooling time and resulting nuclide densities | Missing / not established | Obtain a documented depletion calculation or authoritative data for the exact fuel definition; otherwise remove burnup claim |
| k-effective result is credible | Independent reference value for the same benchmark/model, run settings, uncertainty, convergence and reproducibility records | Two high-budget seeds completed and passed raw-HDF5 audits, but the third seed is incomplete; aggregation was skipped; both source-convergence diagnostics remain DIAGNOSTIC_REVIEW_REQUIRED. No project-specific acceptance band approved | Pre-register a tolerance from the applicable benchmark/reference and uncertainty analysis; never invent an acceptance band after seeing results |
| Fission objective represents a physical decision metric | Definition, normalization, tally uncertainty/covariance, relation to intended metric | Current metric is a relative fission-rate proxy, not absolute power or safety limit | Label as proxy only unless validated conversion and uncertainty are provided |
| Independent review occurred | Reviewer identity/qualification, date, reviewed evidence-manifest hash, findings and disposition | Not yet evidenced | Record an actual review; do not fabricate reviewer approval |

## Update from preserved runs and post-fix smoke audit (2026-10-11)

The canonical high-budget workflow was cancelled after two UMMU seed cases completed 7,000 batches each. Their raw-HDF5 audits passed 22 checks per case; seed 740000 did not complete and the aggregate gate was skipped. Both high-budget logs contained 7,000 entropy-box warnings, so their source-convergence diagnostics remain review-required.

The adapter was corrected to use a wide single axial entropy bin for the 2-D model. The subsequent [corrected-group smoke workflow](https://github.com/thenextw4ng/cb-pfr/actions/runs/38110780563) completed 18 cases (six layouts × three seed rounds) with zero entropy-box warnings, three raw-HDF5 audits passing 112 checks each, three evidence-integrity audits passing 23 checks each, and an independent spatial-mapping audit passing 18/18 cases. This confirms the warning fix at smoke budget only; it does not establish benchmark-grade convergence or physical validity.

Detailed run values and artifact digests are recorded in [the partial high-budget review](C5G7_CANONICAL_HIGH_BUDGET_PARTIAL_RUN_REVIEW_2026-10-11.md) and [machine-readable results](../results/c5g7_canonical_partial_2026-10-11.json). Stage 6 remains open pending line-by-line material review, predeclared acceptance criteria, and independent reactor-physics review.

## Recommended decision path

### Path A — Close a limited UO2/MOX layout integration study

1. Freeze the problem statement: four abstract positions, binary UO2/MOX assignment, exactly two MOX and two UO2. Explicitly state that this is the project's candidate-layout abstraction, not the canonical 16-assembly C5G7 benchmark unless geometry truly matches the specification.
2. Exhaustively enumerate all 16 assignments and prove that exactly six pass the two-and-two constraint.
3. Create a position map from each bit to the generated geometry, and a material map to the exact UO2/MOX datasets actually loaded by OpenMC.
4. Audit generated group boundaries, MGXS hash and provenance, geometry, material IDs, tally support, raw HDF5 statepoints, and run settings for every canonical case.
5. Compare against a reference solution only if it is the same benchmark configuration. If the project's modified layout is not an official benchmark case, describe the comparison as a verification/reference comparison, not a benchmark validation.
6. Define acceptance criteria before selecting a candidate, then rerun with a defensible statistical budget and uncertainty treatment.
7. Ask an independent reactor-physics reviewer to assess the evidence package.

### Path B — Retain the legacy burnup-state QUBO

This path cannot be closed by citations alone. It requires a traceable definition of the three burnup states, including nuclide densities or a reproducible depletion workflow and relevant irradiation history. If those inputs are unavailable, report the mapping as unresolved and do not claim physical validation.

## Required next artifacts

- reports/stage6_evidence_manifest.json: source URLs, access date, revision/table/page, input file hashes, group-edge audit, geometry/material manifest, run IDs, statepoint hashes, and claim-to-evidence links.
- reports/stage6_mapping_contract.json: position map, state-to-material map, composition source, MGXS provenance, reference-comparison protocol, and independent-review record.
- reports/stage6_closure_checklist.md: each requirement marked PASS / FAIL / BLOCKED with a cited artifact.
- Canonical-run evidence bundle with the raw statepoints and machine-readable numerical audit.

## Safety and interpretation boundary

This report is a provenance and verification plan. It does not certify reactor safety, demonstrate a physically optimal fuel loading, or establish that the legacy burnup-state mapping is valid. The public references above are starting points; numerical values must be transcribed and independently checked against the exact applicable specification before use.
