# Stage 6 closure checklist — four-position UO2/MOX study

Updated: 2026-10-11

Legend: PASS = verified by an artifact; BLOCKED = needs further evidence; NOT STARTED = no evidence yet.

- [x] Identify public C5G7 benchmark specification and OpenMC implementation reference.
- [x] Record corrected seven-group edge array in the proposed mapping contract.
- [x] Record current reported MGXS hash as a traceability lead (not as proof of correctness).
- [x] Exhaustively enumerate all 16 four-position binary assignments; exactly six satisfy two UO2 and two MOX. Machine-readable result: reports/stage6_four_position_constraint_audit.json. The same script logic ran locally with exit code 0; GitHub Actions has not yet executed this script.
- [ ] BLOCKED: compare generated materials.xml nuclide densities/material IDs line by line with the selected benchmark material definitions.
- [ ] BLOCKED: verify each candidate string and position order against generated geometry/lattice XML and candidate manifest.
- [x] Re-audit group edges and shared MGXS hash in both completed high-budget seeds; exact standard edges are recorded in the partial-run JSON. The third seed is incomplete; source-convergence review remains open.
- [x] Inspect the two completed canonical statepoint hashes, run settings, and raw-HDF5 audits (22/22 checks each); record the high-budget source-convergence status as DIAGNOSTIC_REVIEW_REQUIRED and the third seed as incomplete.
- [x] Verify candidate-to-generated-lattice and raw mesh-to-assembly mapping for all 18 corrected-group smoke cases; spatial audit PASS. This is structural evidence, not benchmark validation.
- [ ] BLOCKED: line-by-line review of generated material definitions against the applicable primary benchmark specification.
- [ ] BLOCKED: approve comparison protocol and acceptance criteria before declaring any candidate.
- [ ] NOT STARTED: obtain independent reactor-physics review; do not prefill or fabricate approval.
- [x] Explicitly leave legacy fresh/once_burned/twice_burned states unmapped until depletion/isotopic evidence exists.

## Closure definition

The limited integration study can be described as structurally and numerically verified only after the applicable checks pass. It must not be called physically validated until the model/reference scope is appropriate and an independent scientific review supports that claim. A modified four-position layout must not be presented as the canonical C5G7 benchmark merely because it uses C5G7-derived materials.
