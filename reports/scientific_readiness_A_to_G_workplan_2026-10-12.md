# CB-PFR scientific readiness workplan A–G

**Branch:** `feature/scientific-readiness-a-g-hardening`  
**Purpose:** close code/protocol work that can be completed while the canonical UMMU confirmation simulation is pending.  
**Boundary:** this report is an audit/work plan, not a claim that physical validation or simulation convergence has passed.

## Executive summary

Work can proceed in parallel with the canonical high-budget run. The most consequential code-side risk is the interpretation of the 51×51 mesh tally as four 17×17 fuel-assembly blocks. The reducer checks shape, finiteness, non-negativity, and positive integrated rates, but its physical orientation remains an assumption until checked against the actual generated geometry and a benchmark-compatible spatial reference. Synthetic unit tests now exercise the arithmetic contract; they do not certify geometry orientation.

## A. Model identity and provenance

**Can be done now:** compare the pinned upstream source commit, generated geometry/material/settings XML, group boundaries, MGXS provenance, and runtime settings. Record SHA-256 for generated inputs and the actual files used by each run. Diff production and smoke-test XML and explain every physically meaningful difference.

**Evidence required:** machine-readable manifest containing source repository/commit, OpenMC version, geometry/material/settings file hashes, MGXS hash and group boundaries, boundary conditions, run settings, and reviewer status.

**Not yet passed:** a matching hash proves file identity, not fidelity to the primary benchmark specification. Independent specification review remains required.

## B. Mesh-to-assembly tally mapping

The reducer in `scripts/analyze_c5g7_assembly_fission.py` assumes a 51×51 mesh and maps four 17×17 blocks to p00/p01/p10/p11 using explicit x/y slices. It sums the `fission` score and computes max integrated assembly rate divided by mean integrated assembly rate.

**Completed code-side work:** added synthetic contract tests for block indices, integrated arithmetic, layout-to-material labels, excluded non-fuel bins, invalid shape, non-finite/negative values, wrong material count, and zero-rate blocks.

**Still required:** verify mesh lower-left/upper-right, bin ordering, lattice orientation, and actual fuel boundaries against generated geometry and OpenMC filter semantics. Confirm whether the score is an integrated fission-rate tally and document units/normalization. Compare compatible assembly/pin quantities to the primary benchmark reference. Do not call the result absolute power.

## C. QUBO and design-space correctness

The current design study is a four-position assembly-placement reformulation: exactly two UO2 and two MOX, with five reflector positions fixed. It is not the legacy Usmanov burnup-state QUBO.

**Can be done now:** exhaustively enumerate the six layouts; verify the one-hot/material-count constraints and fixed reflector contract; compare QUBO energies/feasibility against direct calculations; test that inconsistent solver metadata and malformed vectors are rejected. Keep physical ranking blocked until a design objective and acceptance criteria are justified.

## D. Data integrity and reproducibility

**Can be done now:** test seed-to-statepoint correspondence, unique hashes, common MGXS and energy-group structure, consistent settings, required fields, and fail-closed behavior for missing/duplicate/corrupt evidence. Preserve exact source commit, input hashes, environment, command line, and generated outputs.

**Important distinction:** unique hashes establish distinct artifacts, not independent physics or correct model identity.

## E. Physical metric and benchmark protocol

**Can be done now:** predeclare score definitions, units, normalization, uncertainty handling, comparison metric, exclusions, and pass/fail/inconclusive logic. Distinguish project screening thresholds from official benchmark acceptance limits. Define how tally uncertainty and between-seed variability are reported.

**Blocked:** selecting a winner or declaring spatial validation before a justified physical objective, trusted spatial reference, and tally mapping are approved.

## F. CI and fail-closed integration

**Can be done now:** run the Python test matrix; test invalid QUBO samples, malformed evidence, missing diagnostics, inconsistent settings, and ranking without a valid physical objective. Verify that incomplete evidence cannot produce a scientifically affirmative status.

**Acceptance evidence:** latest commit's CI checks green, with exact commit SHA recorded. CI has not been claimed green by this report.

## G. Analysis/reporting and release preparation

**Can be done now:** prepare a report schema with per-run uncertainty, between-seed sample SD, reference difference in pcm, comparison z-score with stated assumptions, source-convergence diagnostics, spatial-metric uncertainty, provenance hashes, and explicit limitations. Test reports with synthetic pass/fail/incomplete fixtures.

**Blocked:** final release freeze until model identity review, canonical confirmation, convergence interpretation, and benchmark-compatible spatial validation are resolved or explicitly bounded.

## Terminology for the paper

Prefer **hasil simulasi fisika** for outputs produced by OpenMC, and **validasi fisika** for the process of comparing model/results with a trusted physical benchmark. A completed transport run is not itself proof of physical validation. “Hasil fisik” is understandable but less precise here.

## Current decision

The repository may become **software-tested for the audited contracts** before it becomes **physically validated**. Keep those statuses separate. No reactor-safety certification, no validated absolute power distribution, no winner among six layouts, and no quantum-advantage claim is supported by this workplan alone.
