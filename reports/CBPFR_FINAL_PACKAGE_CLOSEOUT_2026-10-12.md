# CB-PFR final package closeout and claim boundary

**Assessment date:** 2026-10-12  
**Package status:** **95% software/reproducibility handoff target — conditional**  
**Scientific validation status:** **NOT CERTIFIED**  
**Comparison status:** **BLOCKED_NOT_IDENTIFIABLE**  
**Physical winner / CB-PFR superiority:** **NOT ESTABLISHED**

This report closes the current software package at the level supported by existing artifacts. It does not turn an engineering closeout into a physical-validation certificate. The 95% figure refers to package engineering and handoff readiness, not to the proportion of scientific claims proven.

## 1. Evidence directly checked for this closeout

The raw high-budget artifact was available locally and its archive checksum was recomputed:

- Artifact: `cbpfr-c5g7-six-layout-high-budget-confirmation-2026-10-12` (Actions artifact ID `11747677926`).
- Archive SHA-256: `be48b17c2c336a97d08673d191457b9c695853759180116f5382f636b4c93019`.
- ZIP entries: 565; embedded run-level CSV rows: 18; `CASE_RESULT.json` records: 18.
- Embedded CSV SHA-256: `3eb5d575cc5076ead39de04907beddd25fa2310465b508208579bbd4a5c0192d`.
- Coverage: six layouts (`MMUU`, `MUMU`, `MUUM`, `UMMU`, `UMUM`, `UUMM`) × three rounds (`820000`, `830000`, `840000`).
- Distinct seeds: 18; distinct statepoint hashes: 18; common MGXS SHA-256: `a4328a7b012321fbe8f661745aa135f0a2eecd34cf475429e160865204acb129`.
- Run table records common settings: 7,000 total batches, 500 inactive batches, 10,000 particles/batch, two threads; all rows mark the group-structure audit `PASS`.
- The archived proxy extraction audit reports a maximum absolute difference of `2.22e-16` between reconstructed and exported relative assembly-integrated fission-rate peaking values.

These are archive/provenance/extraction checks. They do not independently certify the physical model or convergence.

## 2. Reproducible commands

Run from the repository root with Python 3.10+:

```bash
python -m unittest discover -s tests -v
python scripts/audit_high_budget_archive.py /path/to/cbpfr-high-budget-raw.zip \
  --bridge-csv results/cbpfr_physical_feasibility_bridge_2026-10-12.csv \
  --json results/cbpfr_high_budget_archive_audit.json
python scripts/audit_cbpfr_comparison_readiness.py \
  results/c5g7_six_layout_confirmation_2026-10-12/run_level_results.csv \
  --json results/cbpfr_comparison_readiness_2026-10-12.json
```

The high-budget archive audit checks case records, seed/settings provenance, statepoint/MGXS hashes, and compares the embedded source CSV with the bridge CSV when `--bridge-csv` is supplied. The comparison-readiness audit is intentionally fail-closed. The saved comparison report currently blocks a confirmatory comparison; that is the correct behavior, not a software failure.

Latest recorded automated CI for commit `cc1e39dc288036bf2961ee8ee04ee6f5f37fe084` passed on Python 3.10, 3.11, and 3.12: https://github.com/thenextw4ng/cb-pfr/actions/runs/38266411572. Re-run the commands above on the final checkout and retain their stdout/JSON as release evidence before tagging a release.

## 3. Claims safe to publish now

The following wording is supportable with the current package and must remain bounded to this study:

1. **Method/software claim.** “We implemented CB-PFR as an uncertainty-aware, post-optimization candidate-screening and ranking layer. Its operational bounds are not automatically calibrated confidence intervals or safety margins.”
2. **QUBO formulation claim.** “For the six four-position layouts containing exactly two MOX and two UO₂ assemblies, the composition-only objective (E(y)=A(\sum_i y_i-2)^2) assigns equal energy to every feasible layout. It enforces composition but cannot rank their physical performance.”
3. **Archived-computation claim.** “An archived campaign contains 18 completed OpenMC runs covering six layouts over three seed rounds, with distinct recorded seeds and statepoint hashes and a shared recorded MGXS hash.”
4. **Extraction claim.** “Reconstruction of the relative assembly-integrated fission-rate peaking proxy from the saved mesh tally reproduces the exported values to a maximum absolute discrepancy of approximately (2.22\times10^{-16}).”
5. **Exploratory-selection claim.** “In a three-fold leave-one-seed-round-out descriptive analysis, the proxy-based selector chose MMUU in all three folds with zero observed held-out regret on that same proxy.” Immediately disclose that this is exploratory, based on only three rounds, and does not certify a physically acceptable or optimal configuration.
6. **Negative result.** “The existing synthetic confirmatory benchmark did not meet its predeclared practical-effect threshold: pooled gain was +0.4875 percentage points against a threshold of at least 2 percentage points.” Do not omit this result when discussing the synthetic benchmark.
7. **Comparison limitation.** “A fair confirmatory claim of CB-PFR superiority over QUBO-only is not identifiable from the current evidence: the composition-only QUBO ties the candidate set, there is no comparable pre-physics score table that ranks all layouts, no approved physical acceptance rule, and only three exploratory seed rounds.”

### Suggested concise abstract/result wording

“CB-PFR was implemented as an uncertainty-aware post-optimization screening layer and evaluated against a four-position C5G7 layout study. The composition-only QUBO enforces the two-MOX constraint but ties all six feasible layouts. An archived set of 18 OpenMC runs (six layouts, three seed rounds) supports reproducible extraction of a relative assembly-integrated fission-rate peaking proxy; raw tally reconstruction agreed with the exported values to (2.22\times10^{-16}) maximum absolute discrepancy. An exploratory leave-one-round-out analysis selected MMUU in all three folds with zero observed proxy regret. However, the endpoint is a relative fission-rate proxy rather than absolute power or a safety criterion, and the small number of rounds, unresolved independent model/tally review, lack of an approved physical acceptance rule, and absence of a comparable pre-physics QUBO ranking preclude claims of physical validation or CB-PFR superiority. The confirmatory synthetic benchmark also failed its predeclared practical-effect threshold. These results establish a reproducible software and screening workflow, not a certified physical winner.”

## 4. Claims explicitly prohibited by current evidence

Do **not** claim any of the following:

- reactor safety, licensed power peaking, absolute power validation, or validation for an operating reactor;
- complete C5G7 benchmark validation or convergence certification for all six layouts;
- CB-PFR statistical superiority or generalization beyond the exploratory candidate set;
- that the current composition-only QUBO optimizes physical performance;
- quantum advantage or quantum-hardware execution;
- that the synthetic benchmark demonstrates nuclear-physics validity.

The canonical UMMU scalar (k_{eff}) comparison is only a screening comparison against the saved reference; scalar agreement alone is not spatial/model validation. The relative fission-rate proxy must not be renamed absolute power.

## 5. Final checklist

| Item | Closeout disposition |
|---|---|
| Frozen six-layout candidate set and stated two-MOX/two-UO₂ composition | Present in study artifacts |
| Raw run archive and checksums | Archive locally checksum-verified; keep a durable release copy |
| 18-row coverage, seed uniqueness, common recorded settings/MGXS | Table-level checks pass |
| Raw tally → relative proxy arithmetic | Reported audit passes to floating-point precision |
| QUBO algebraic regression tests and cross-version CI | Recorded CI passes on Python 3.10–3.12 |
| CB-PFR implementation as software | Present; heuristic bounds must remain explicitly labelled |
| Comparison readiness gate | Runs fail-closed as intended; comparison remains blocked |
| Independent geometry/material/tally review | **OPEN** |
| Full six-layout source-convergence certification | **OPEN** |
| Approved, prospectively justified physical acceptance rule | **OPEN** |
| Prospective independent confirmation rounds and fair baseline comparison | **OPEN** |
| Publication claim boundary and negative result disclosure | Defined in this report |

## 6. Release decision

**Software package: ready for a final reproducibility pass and versioned handoff, subject to rerunning the commands above on the exact release commit.** Do not call the package “physically validated.”

**Scientific result: report as a methodological software/screening study with exploratory C5G7 evidence and explicit unresolved gates.** A stronger physical-performance conclusion requires independent model/tally sign-off, a justified predeclared physical acceptance rule, documented source-convergence review, and prospective independent confirmation data. These are scientific prerequisites; they cannot be replaced by adding more UI, renaming metrics, or changing thresholds after inspecting outcomes.
