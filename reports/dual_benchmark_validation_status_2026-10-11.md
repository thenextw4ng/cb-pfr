# Dual-benchmark validation status: C5G7 + BEAVRS

## Decision

Use separate, complementary evidence streams; do not merge their geometries or infer that one benchmark validates the other.

- **C5G7** remains the computational transport benchmark and the place to test the six 2x2 UO2/MOX layout candidates.
- **BEAVRS** is now the selected experimental benchmark pathway. A pinned full-core model runner and GitHub Actions workflow compare the Cycle 1 day-0 normalized radial detector map with calculated mesh-integrated assembly fission rates. This workflow has been added and triggered; its actual run result and raw artifact audit are still required before reporting a completed comparison.
- **KRITZ-2** is deferred and is not the active validation pathway.
- Neither benchmark validates the legacy fresh/once-burned/twice-burned QUBO mapping automatically.

## Critical model check

A public KRITZ-2 OpenMC example was found, but it builds a **single pin cell with reflective boundaries**, i.e. an infinite-lattice calculation. Its own analysis compares that result against participant mean values for the experimental cores. That comparison is not sufficient for finite-core experimental validation: a pin-cell result and a finite-core measured/evaluated k-effective are not the same modeled quantity. We should not import that comparison as a passing validation result.

## Execution gates

1. Re-run and audit the corrected-group canonical C5G7 case with independent high-budget seeds; the existing 18 corrected-group smoke runs are exploratory, not a convergence certificate.
2. Execute the BEAVRS workflow, audit its statepoint, 58 detector-bin mapping, nuclear-data provenance, and comparison output; resolve or quantify the bank-E insertion mismatch and add uncertainty-aware acceptance criteria.
3. Keep the C5G7 candidate-ranking result and BEAVRS experimental comparison as distinct evidence streams. Do not claim that a BEAVRS map comparison validates all six C5G7 layouts or the legacy QUBO mapping.
4. Independently test CB-PFR effectiveness on a defensible physical candidate pool with a common evaluation budget.

## Reference

OECD Nuclear Energy Agency, *Benchmark on the KRITZ-2 LEU and MOX Critical Experiments*, NEA/NSC/DOC(2005)24 (2006): https://www.oecd-nea.org/upload/docs/application/pdf/2020-01/nsc-doc2005-24.pdf

**Current status: BEAVRS workflow committed and triggered; experimental comparison is not yet verified as complete. Full CB-PFR physical validation and quantum-device evidence remain unestablished.**


## BEAVRS workflow links

- [BEAVRS comparison protocol](BEAVRS_CYCLE1_EXPERIMENTAL_COMPARISON_PROTOCOL.md)
- [Runner](../scripts/run_beavrs_cycle1_map_validation.py)
- [GitHub Actions workflow](../.github/workflows/beavrs-cycle1-map-validation.yml)
- [Run 1](https://github.com/thenextw4ng/cb-pfr/actions/runs/38116211696)
- [Run 2](https://github.com/thenextw4ng/cb-pfr/actions/runs/38116218368)
