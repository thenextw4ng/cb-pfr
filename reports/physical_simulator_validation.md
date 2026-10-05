# Physical Simulator Validation Report

## Evidence classification

**Achieved:** Level A software verification plus limited benchmark comparison.  
**Not achieved:** full benchmark verification and CB-PFR physical-hypothesis validation.

The executed simulator record concerns an MC/DC C5G7 transport benchmark. It is retained as execution evidence only; it is not a physical CB-PFR validation.

## Recorded runs

| Histories | k_eff ± reported s.d. |
|---:|---:|
| 750 | 1.0948691 ± 0.0606149 |
| 2,500 | 1.1946246 ± 0.0307324 |
| 3,000 seed 101 | 1.2235257 ± 0.0361822 |
| 3,000 seed 102 | 1.2296893 ± 0.0306899 |
| 3,000 seed 103 | 1.1353817 ± 0.0459202 |
| 4,000 | 1.1982456 ± 0.0396033 |
| 12,000 | 1.1656486 ± 0.0168994 |

The equal-settings three-seed group has mean 1.1961989, sample SD 0.0527593, and SE 0.0304606. No source-convergence plateau is claimed.

## Reference boundary

A preserved high-history reference is approximately 1.16562 ± 0.02% at 50 million histories. The 12,000-history run is numerically compatible, but this is not validation: its uncertainty is much larger and the benchmark execution is separate from CB-PFR candidate evaluation.

## OpenMC decision

No OpenMC model, executable, or cross-section library was available for a mapped CB-PFR experiment. Adding OpenMC would not solve the missing QUBO-to-physics mapping by itself.

## Conclusion

Real simulator execution is documented. Full physical CB-PFR validation is **not established**.
