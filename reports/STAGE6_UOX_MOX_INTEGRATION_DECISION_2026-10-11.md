# Stage 6 — UO2/MOX integration path A decision (2026-10-11)

## Decision and scope

Proceed with the **separate four-position UO2/MOX layout formulation**. This is a limited layout-integration study, not a conversion of the legacy three-state burnup QUBO.

The repository's legacy model in `src/cbpfr/qubo.py` defines three categorical labels: `fresh`, `once_burned`, and `twice_burned`. Those labels remain unmapped. The separate C5G7 layout study uses four assembly positions, each assigned either UO2 or MOX, with exactly two of each. Do not describe these two formulations as the same QUBO unless a separately reviewed mathematical transformation is implemented.

## Evidence already available

- Primary benchmark specification: OECD/NEA, *Benchmark specification for Deterministic 2-D/3-D MOX Fuel Assembly Transport Calculations Without Spatial Homogenization* (NEA/NSC/DOC(2001)4): https://harbor.oecd-nea.org/upload/docs/application/pdf/2020-01/nsc-wpfc-doc2012-16.pdf
- OpenMC multigroup C5G7 implementation example: https://docs.openmc.org/en/v0.12.2/examples/mg-mode-part-i.html
- OECD/NEA C5G7-TD benchmark overview: https://oecd-nea.org/jcms/pl_32145/deterministic-time-dependent-neutron-transport-benchmark-without-spatial-homogenisation-c5g7-td
- Repository input-provenance comparison: `results/c5g7_input_provenance_comparison_2026-10-11.json`. It records that geometry, tallies, plots, and the MGXS data compared equal to the pinned MIT CRPG source after expected cross-section path normalization; settings differ in run budget and seed as expected. Its own conclusion says this is not benchmark certification and still requires review against the primary specification.
- Structural mapping audit: `reports/C5G7_SPATIAL_MAPPING_AUDIT_2026-10-11.md`, 18 smoke cases passed geometry/lattice and raw HDF5 tally-support checks; physical validation was explicitly not established.
- Exhaustive count audit: `reports/stage6_four_position_constraint_audit.json`, 16 assignments checked, six satisfy the two-UO2/two-MOX constraint.

## Four-position combinatorial result

Position signature order is currently documented as P1=top-left, P2=top-right, P3=bottom-left, P4=bottom-right. The six count-feasible signatures are:

`UUMM, UMUM, UMMU, MUUM, MUMU, MMUU`

This order must still be checked against each generated lattice/candidate manifest before a signature is interpreted as a physical location map. The enumeration proves the count constraint only.

## Explicit mapping policy

- `U` means the UO2 material ID and nuclide-density vector actually loaded by the generated OpenMC model.
- `M` means the specific MOX material/enrichment ID and nuclide-density vector actually loaded by that model.
- Use the selected material definitions from the pinned C5G7 source and compare them to the generated `materials.xml`. Do not substitute material data from a different MOX benchmark simply because it is public.
- Seven-group boundaries in the corrected study are `[1e-5, 0.0635, 10, 100, 1000, 500000, 1000000, 20000000]` eV. The canonical artifact must be re-audited for the exact array and MGXS provenance.
- A modified four-layout permutation study can be a C5G7-derived model; call it the canonical benchmark only if every applicable geometry, material, boundary, and specification requirement matches the reference case.
- Fission-peaking is a relative tally proxy, not absolute power or a safety metric.

## Remaining closure gates

1. Inspect the canonical high-budget artifact and its raw statepoints when the workflow finishes.
2. Audit generated `materials.xml` material IDs and nuclide densities against the pinned source and benchmark specification.
3. Confirm candidate string order against actual generated lattice XML/manifests.
4. Predeclare a comparison protocol and acceptance criteria from an applicable reference and uncertainty budget. Do not select the criteria after viewing candidate ranks.
5. Complete independent reactor-physics review with reviewer, date, evidence-manifest hash, findings, and disposition.
6. Run the new constraint audit in CI and preserve its output.
7. Keep the legacy burnup-state QUBO mapping marked unresolved.

## Current status

**PARTIALLY IMPLEMENTED — NOT PHYSICALLY VALIDATED.** Public reference data are acceptable for a source-traceable implementation, but citations alone do not complete material-by-material verification, convergence/uncertainty analysis, acceptance criteria, or independent review. No winner is declared.
