# Dual-benchmark validation status: C5G7 + KRITZ-2

## Decision

Use both benchmarks as complementary evidence, not as one merged reactor model.

- **C5G7** remains the computational transport benchmark and the place to test the six 2x2 UO2/MOX layout candidates.
- **KRITZ-2** supplies independent experimental validation evidence for a model that reproduces the experimental configurations. The official OECD/NEA report includes UO2 cases KRITZ-2:1 and :13 and the MOX case KRITZ-2:19 at cold and hot conditions.
- Neither benchmark validates the legacy fresh/once-burned/twice-burned QUBO mapping automatically.

## Critical model check

A public KRITZ-2 OpenMC example was found, but it builds a **single pin cell with reflective boundaries**, i.e. an infinite-lattice calculation. Its own analysis compares that result against participant mean values for the experimental cores. That comparison is not sufficient for finite-core experimental validation: a pin-cell result and a finite-core measured/evaluated k-effective are not the same modeled quantity. We should not import that comparison as a passing validation result.

## Execution gates

1. Re-run and audit the corrected-group canonical C5G7 case with independent high-budget seeds; the existing 18 corrected-group smoke runs are exploratory, not a convergence certificate.
2. Implement and audit a KRITZ-2 finite-core model from the official specification, including rod-array dimensions, moderator level/leakage treatment, boron, hot/cold conditions, and traceable material compositions.
3. Run the KRITZ-2 model and compare only like-for-like quantities to the official evaluated experiment. Report residuals and uncertainty separately.
4. Keep the C5G7 candidate-ranking result and KRITZ experimental validation as distinct evidence streams. Do not claim that passing KRITZ validates all six C5G7 layouts or the legacy QUBO mapping.

## Reference

OECD Nuclear Energy Agency, *Benchmark on the KRITZ-2 LEU and MOX Critical Experiments*, NEA/NSC/DOC(2005)24 (2006): https://www.oecd-nea.org/upload/docs/application/pdf/2020-01/nsc-doc2005-24.pdf

**Current status: integration design recorded; physical KRITZ-2 validation is not yet executed or passed.**
