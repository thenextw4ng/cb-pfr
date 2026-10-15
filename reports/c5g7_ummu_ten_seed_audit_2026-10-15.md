# C5G7 corrected-mesh UMMU replication: ten-seed audit

**Audit date:** 15 October 2026
**Source runs:** `38714545029` (six initial runs) and `38723127815` (seven additional seeds per protocol; overall GitHub Actions conclusion is `cancelled`).
**Model:** UMMU, OpenMC 0.16.0; 7,000 batches; 10,000 particles/batch; Protocol A = 500 inactive batches; Protocol B = 100 inactive batches.

## Conclusion

**The ten-seed-per-protocol dataset is complete at the artifact/evidence level: 20 of 20 statepoints were independently inspected, with 10 unique seeds per protocol.** For every run, the case and physical result report completed; the statepoint exists and its SHA-256 matches the run's `output_hashes_after_run`; `settings.xml`, statepoint seed/batch/inactive metadata agree; the two-dimensional x-y mesh is 51×51 and covers the modeled core bounds; and both the mesh audit and OpenMC log record zero `Fission source site(s) outside of entropy box` warnings. Within each protocol, all ten statepoint hashes and source-bank hashes are distinct, while geometry and MGXS hashes remain constant.

**Workflow-status caveat:** GitHub marks extension run `38723127815` as `cancelled`. In particular, the Protocol B seed `7720000` job is labelled cancelled even though its captured job log shows the simulation completed, the mesh audit had zero warnings, a nonempty 1,113,488-byte statepoint was present, and the artifact upload completed. It was counted only after checking that per-seed evidence, not based on the job badge.

**Scientific gate remains open:** every audit row preserves `convergence_certified=false`. Complete, warning-free artifacts do not by themselves certify source convergence, statistical independence of batch traces, official benchmark acceptance, physical validation, or layout optimality.

## Per-protocol summary

| Metric | Protocol A — 500 inactive | Protocol B — 100 inactive |
|---|---:|---:|
| Verified runs / target | 10/10 | 10/10 |
| Mesh warnings | 0 | 0 |
| Distinct statepoints | 10 | 10 |
| Mean k-effective | 1.186510134 | 1.186470290 |
| Mean difference to archived reference 1.18655 (pcm) | -3.99 | -7.97 |
| Between-run sample SD (pcm) | 12.85 | 16.32 |
| Pooled within-run SD (pcm) | 9.67 | 9.42 |
| Between/within SD ratio | 1.329 | 1.732 |
| Mean k-generation Q4−Q1 (pcm) | -7.71 | -23.75 |
| Per-seed k-generation Q4−Q1 range (pcm) | -114.55 to +65.05 | -96.35 to +23.49 |
| Mean lag-1 entropy ACF | 0.704 | 0.706 |

The archived value 1.18655 is used as a descriptive comparator only, not as evidence of official benchmark acceptance. Between-run SD is the sample standard deviation of seed-level k-effective estimates; pooled within-run SD is the root mean square of the per-run statistical SDs. The lag-1 autocorrelation is computed on active-batch entropy traces after removing the protocol's inactive batches.

## Interpretation

1. The initial three-seed Protocol B sample suggested under-dispersion; in the ten-seed summary this is no longer observed (between-run SD 16.32 pcm versus pooled within-run SD 9.42 pcm; ratio 1.73). This does not alone prove statistical calibration.
2. Entropy lag-1 autocorrelation remains high at about 0.70 in both protocols. Consecutive batch entropy values should not be treated as independent observations.
3. Seed-level k-generation Q4−Q1 shifts vary substantially. A mean close to zero does not erase large shifts in individual runs; use the per-run CSV and review full traces against predeclared tolerances.
4. Safe conclusion: **the ten-seed replication data and mesh-integrity checks are complete; convergence/reliability is not certified.**

## Seed list

Both protocols contain seeds: `720000`, `730000`, `740000`, `1720000`, `2720000`, `3720000`, `4720000`, `5720000`, `6720000`, `7720000`.

## Detailed evidence

- Run-level measurements and hashes: `results/c5g7_ummu_ten_seed_audit_2026-10-15.csv`.
- The original statepoints, settings, logs, and mesh audits remain available in their GitHub Actions artifacts.