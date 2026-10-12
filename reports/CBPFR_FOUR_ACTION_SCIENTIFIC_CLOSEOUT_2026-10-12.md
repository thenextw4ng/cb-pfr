# CB-PFR Four-Action Scientific Closeout — 2026-10-12

## Decision summary

**Compute and run-evidence integrity pass. Internal model/tally audit is partial. Physical validation is not certified. No winner is selected. CB-PFR superiority is not established.**

Workflow: https://github.com/thenextw4ng/cb-pfr/actions/runs/38229045726

The completed campaign contains 18 OpenMC runs: six fuel layouts × three independent seed rounds. Each run used 7,000 batches (500 inactive), 10,000 particles per batch, and two threads. The combined raw artifact SHA-256 is `be48b17c2c336a97d08673d191457b9c695853759180116f5382f636b4c93019`; exported CSV SHA-256 is `3eb5d575cc5076ead39de04907beddd25fa2310465b508208579bbd4a5c0192d`.

## Action 1 — Model and tally review

### Internal checks completed
- The run export records pinned upstream source commit `ba41bee54320ada0b4ac39a0dd2ca3c1d090a450`, shared model-builder hash, common MGXS SHA-256, corrected seven-group boundaries, common run settings, and unique statepoint hashes/seeds.
- The design manifest enumerates six four-position layouts, each with two MOX and two UO₂, while retaining the five reflector positions.
- The tally mesh is 51 × 51 across 64.26 cm: 1.26 cm mesh bins. Each assembly block is 17 × 17 bins, geometrically consistent with 17 × 17 pin assemblies at 1.26 cm pitch.
- The analysis aggregates four fuel-assembly regions and defines the proxy as `max(assembly-integrated fission rate) / mean(assembly-integrated fission rate)`.

### Not signed off
This is an internal code/data audit, **not independent expert validation**. An external reviewer still needs to compare generated geometry/material/boundary inputs and tally mapping against the primary OECD/NEA C5G7 specification and an appropriate reference tally. The reported proxy is not absolute power.

### Convergence caution
The archived smoke-to-high-budget comparison reports mean `k_eff` shifts of roughly 0.0004–0.0032 in magnitude for several layouts, while high-budget within-run SD is about 0.000095. Since budgets and seeds differ, this is not a paired convergence test; however, the shifts are large enough that convergence must remain uncertified and smoke-model provenance should be reviewed.

## Action 2 — Decision rule frozen (fail-closed)

No numeric physical acceptance threshold is invented from observed results. The frozen rule is: **no winner unless** (1) independent model/tally review is signed off, (2) a model-appropriate `k_eff` and relevant tally criterion are justified from primary specifications before final ranking, (3) uncertainty treatment is documented, and (4) a candidate passes every predeclared criterion. If any gate is unresolved, return `NO_SELECTION / INCONCLUSIVE`.

Numeric limits and CB-PFR weights must be sourced and approved independently, not tuned to force a winner.

## Action 3 — Fair comparison status

An exploratory leave-one-seed-round-out check was run on the fission-rate proxy: select the lowest mean proxy from two rounds, then evaluate that selected layout on the held-out round. MMUU was selected in all three folds and also had the lowest proxy in each held-out round. This supports only descriptive stability of this proxy ranking within this six-layout sample. It is not an independent physical truth test because selection and evaluation use the same proxy, only three seed rounds exist, and the layouts have not passed independent physical validation.

A fair **CB-PFR vs QUBO-only superiority test remains blocked**: the completed evidence artifact does not contain an independently justified, predeclared physical acceptance rule and comparable pre-physics QUBO objective scores for each layout. The material-placement QUBO and post-physics selector QUBO are distinct formulations. Do not fabricate a QUBO score or call the post-physics selector evidence for pre-physics optimization superiority.

After the criteria are approved, compare CB-PFR, QUBO-only, and a simple baseline on identical candidate sets using predeclared held-out seeds. Preserve negative and inconclusive results.

## Action 4 — Reproducibility freeze

A closeout bundle retains the run-level CSV, export audit, objective audit, budget comparison, a machine-readable closeout JSON, and the raw run artifact. The raw artifact must be copied to a durable research repository/release before GitHub Actions retention expires; verify its checksum after transfer. Pin the source commit, environment, exact command lines, and artifact checksums in the final deposit.

## Current status

| Gate | Status |
|---|---|
| Compute execution | PASS |
| Run evidence integrity | PASS |
| Internal model/tally audit | PARTIAL; external sign-off required |
| Numeric physical acceptance limits | NOT APPROVED; fail-closed rule frozen |
| Proxy holdout ranking | DESCRIPTIVE ONLY |
| CB-PFR superiority | NOT ESTABLISHED |
| Physical validation | NOT CERTIFIED |
| Winner | NONE |

This is a computational screening package prepared for independent review, not a certified physical validation or reactor-safety assessment.
