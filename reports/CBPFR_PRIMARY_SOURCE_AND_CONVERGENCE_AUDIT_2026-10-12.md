# C5G7 independent-source audit and next-run gate — 2026-10-12

## Purpose and scope
This report separates (i) canonical C5G7 benchmark fidelity, (ii) numerical convergence, (iii) physical acceptance decisions, and (iv) the algorithm comparison. Passing one does not imply the others. This is a software research screening study, not reactor licensing or safety analysis.

## Primary-source review
The OECD/NEA primary report is *Benchmark on Deterministic Transport Calculations Without Spatial Homogenisation: A 2-D/3-D MOX Fuel Assembly Benchmark*, NEA/NSC/DOC(2003)16:
- Official PDF: https://www.oecd-nea.org/upload/docs/application/pdf/2019-12/nsc-doc2003-16.pdf
- NEA record: https://www.oecd-nea.org/jcms/pl_13548/benchmark-on-deterministic-transport-calculations-without-spatial-homogenisation
OpenMC's own methods documentation explains that eigenvalue calculations require both eigenvalue and fission-source convergence; source convergence can be slower:
- https://docs.openmc.org/en/stable/usersguide/settings.html
- https://docs.openmc.org/en/stable/methods/eigenvalue.html

A published description of the canonical C5G7 quarter-core states a 64.26 × 64.26 cm model, four 21.42 cm assemblies, 17×17 pin lattices at 1.26 cm pitch, seven groups, reflective bottom/left and vacuum top/right boundaries, with the canonical UO2/MOX placement and reference k-effective 1.186550: https://tdb.oecd-nea.org/upload/docs/application/pdf/2019-12/nsc-doc2003-16.pdf.

## Critical distinction: benchmark case vs study variants
The six strings MMUU, MUMU, MUUM, UMMU, UMUM, UUMM are permutations of two MOX and two UO2 assemblies. Only the layout that exactly matches the canonical benchmark material placement and all its material/boundary/model assumptions can be directly compared to the canonical reference k-effective. The reference value 1.186550 is not a universal acceptance target for all six variants. Any prior report that applied the canonical scalar reference to a non-canonical permutation must label that comparison exploratory/non-applicable until the exact layout mapping is reconciled against the benchmark drawing and the model manifest.

The mesh arithmetic is consistent: 64.26 cm / 51 = 1.26 cm per mesh bin; 17 bins span one 21.42 cm assembly. Arithmetic consistency alone does not verify orientation, indexing, tally filter, material ownership, omitted/duplicated bins, normalization, or whether fission-rate is a proxy for power.

## Evidence reviewed from the saved campaign
The saved table records 18 runs (six layouts × three seed rounds), common settings (7000 total batches, 500 inactive, 10,000 particles/batch, two threads), unique seeds/statepoint hashes, one MGXS hash and a seven-group structure audit marked PASS. This establishes table/provenance consistency only.

### Mandatory independent model/tally checklist
A reviewer should mark each item PASS/FAIL/UNRESOLVED with source line or artifact:
1. Geometry extents and boundaries against primary benchmark.
2. Exact assembly-to-material mapping for canonical case and each study permutation.
3. Pin/lattice dimensions, guide tubes, instrumentation tubes, water gaps, and material IDs.
4. Temperature/material data and seven-group cross-section library provenance/hash.
5. Mesh bounds/dimensions, filter order, score, tally estimator and cell/mesh overlap.
6. Correct mapping from 51×51 bins to 3×3 assembly-level tally regions (17×17 bins each), with explicit index/orientation test against a hand-built synthetic field.
7. Distinguish integrated fission rate, normalized relative shape, assembly power and absolute power; do not label the first as the last.
8. Compare canonical observable with a like-for-like reference and state uncertainty/covariance assumptions.
9. Record reviewer, date, model commit, MGXS hash and disposition.

The current evidence package does not contain an independent signed review for these items. Therefore the disposition is **PARTIAL / EXTERNAL REVIEW REQUIRED**, not a pass.

## Convergence audit: what evidence is and is not available
The high-budget campaign used 500 inactive batches. This count is not itself proof of source convergence. OpenMC guidance explicitly recommends examining source-distribution convergence (often Shannon entropy) as well as k-effective; k-effective may stabilize earlier. The available summary table has aggregate run values, not the per-generation entropy/source history needed for a defensible trend analysis of all six layouts. Thus convergence cannot be retrospectively certified from the table alone.

### Required next computational run
For each of the six layouts, preserve per-batch k-effective and source entropy (use an entropy mesh covering all fissionable regions), then:
- plot running/cumulative k-effective and entropy against batch;
- compare early vs late active-batch windows, with autocorrelation-aware uncertainty if practical;
- document the inactive-batch choice before interpreting active tallies;
- repeat at least one representative layout with longer inactive batches and independent seeds to check source-start sensitivity;
- retain statepoint, summary, settings XML, model XML, cross-section library metadata, stdout/stderr, and exact command/environment hashes.
Do not declare convergence solely because the final k-effective is stable. Do not use an arbitrary universal numerical entropy slope as an acceptance threshold; predeclare the diagnostic procedure and explain its model-specific interpretation.

## Gate 2: physical acceptance rule
The existing fail-closed rule is retained:
- No winner until model/tally review is signed off.
- Use benchmark tolerances only for the exact benchmark observable/case they apply to; use prospectively justified criteria for study variants.
- Keep per-run Monte Carlo uncertainty, between-seed variability, and reference uncertainty distinct.
- Missing or incomparable criterion => NO_SELECTION / INCONCLUSIVE.
- Any post-result changes are exploratory and require a fresh holdout for confirmatory claims.

The template at `protocols/cbpfr_physical_decision_rule_TEMPLATE_NOT_APPROVED.json` intentionally contains no numeric thresholds and remains unapproved. The canonical reference k-effective is a benchmark comparison, not a safety criterion.

## Gate 3: what is a fair QUBO-only comparison?
The pre-physics composition QUBO `A*(sum(y_i)-2)^2` assigns the same energy to all six exactly-two-MOX layouts. It is a feasibility encoding, not a physical optimizer. No post-physics selector energy may be presented as if it were a pre-physics objective.

A fair experiment should answer a narrower, identifiable question: **does the CB-PFR physical-feedback selection layer choose better candidates than a prespecified no-physics selection policy under the same candidate set and OpenMC evaluation budget?**

Predeclare:
- Methods: CB-PFR selector; random feasible candidate with fixed seeds; and any genuine pre-physics objective/optimizer only if its objective is specified independently of physical outcomes. If the QUBO only encodes composition, report it as a tie baseline and state the tie-breaking rule.
- Candidate set and model/MGXS hashes frozen before held-out seeds.
- Primary endpoint: proportion of selections passing the approved physical rule; secondary endpoints: best accepted objective/proxy, regret, run-to-run stability, number of OpenMC evaluations and wall/CPU time.
- Equal physical-evaluation budget for each method; all failures and rejected candidates count.
- Tune weights/thresholds on training seeds only. Confirm on new, independent seed rounds not used in tuning.
- Analyze uncertainty and ties; report results even if CB-PFR loses.

The current three rounds are exploratory and reuse the same fission-rate proxy for selection/evaluation. They cannot establish superiority. Since the feasible composition QUBO has no ranking signal, a numerical CB-PFR-vs-QUBO-only performance delta is not identifiable until a meaningful pre-physics objective or a precise tie-baseline protocol is defined.

## Gate 4: reproducibility freeze
Current workflow artifact `cbpfr-c5g7-six-layout-high-budget-confirmation-2026-10-12` (artifact ID 11747677926, 20,977,710 bytes) was listed as not expired when inspected. This is not a durable archive guarantee. Download it, verify the published SHA-256 manifest, and publish the evidence bundle to a versioned GitHub release or another durable repository before workflow retention expires. Include the original raw artifact rather than only derived CSVs, source/model commit, MGXS hash, environment and commands, analysis code, outputs and a manifest.

## Disposition after this audit
- Run-table integrity: PASS.
- Canonical benchmark mapping: UNRESOLVED pending source-to-model review.
- Mesh arithmetic: PASS; tally semantics/mapping: UNRESOLVED.
- Six-layout source convergence: NOT CERTIFIED because per-batch source diagnostics are absent from the summary evidence.
- Numeric physical acceptance limits: NOT APPROVED.
- CB-PFR superiority: NOT ESTABLISHED; current comparison BLOCKED/NOT IDENTIFIABLE.
- Selected winner: NONE.
- Physical validation: NOT CERTIFIED.

## Approved wording
“We performed a reproducible six-layout C5G7/OpenMC screening campaign. Run provenance and mesh-dimension arithmetic checks passed. Canonical benchmark mapping, independent tally review, and source-convergence assessment remain open; the available results do not certify full physical validation or establish CB-PFR superiority over a no-physics/QUBO baseline.”
