# Stage 5–6 checkpoint — 2026-10-11

## Stage 5: CB-PFR + layout-QUBO selection

Status: selection software is implemented, but a real-data selection is blocked. The selector requires six layouts, at least three unique seeds per layout, unique statepoint hashes, a common MGXS hash, corrected C5G7 group boundaries, identical run settings, adequate run budgets, and user-approved physical criteria. The available 18-run study is smoke-budget evidence only. No design-specific acceptable (k_{eff}) interval has been approved, so no physical winner is declared.

Canonical high-budget workflow 38103032861 was cancelled after two independent UMMU cases completed 7,000 batches each. Their statepoints and raw-HDF5 audits were preserved in artifact 11691113062; both raw audits passed 22 checks. The third seed did not complete, the aggregate gate was skipped, and both completed logs contain repeated entropy-box warnings. The source-convergence diagnostic remains `DIAGNOSTIC_REVIEW_REQUIRED`. See `reports/C5G7_CANONICAL_HIGH_BUDGET_PARTIAL_RUN_REVIEW_2026-10-11.md`. Do not claim a completed three-seed run or convergence PASS.

## Stage 6: legacy QUBO-to-physics mapping

Status: fail-closed audit. The five required mapping fields in `config/benchmarks/c5g7_manifest.json` are null: position map, state-to-material map, material-composition source, cross-section provenance, and reference-comparison protocol. Applying `scripts/audit_c5g7_mapping_contract.py` therefore yields `NO_DEFENSIBLE_MAPPING_FOUND`; independent review is not passed and physical mapping cannot be claimed.

The separate four-variable QUBO only encodes exactly two MOX and two UO2 assemblies. It does not map `fresh / once_burned / twice_burned` to C5G7 materials.

## Next steps

1. Finish and inspect run 38103032861 and its artifacts.
2. Approve a study-specific k_eff interval, objective, and tally normalization before final ranking.
3. Run the six layouts at a common, justified higher budget with repeated seeds and audited provenance.
4. Execute the selector on that complete dataset and preserve its JSON status.
5. Keep legacy mapping blocked until traceable depletion/isotopic data and independent review are available.

**Conclusion:** selection software exists; physical validation and the legacy burnup-state mapping are not established. No reactor-safety claim or physical optimum is asserted.
