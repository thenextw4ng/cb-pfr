# CB-PFR Existing-Experiment Analysis and Simulation Decision

**Date:** 2026-10-12  
**Branch:** `research/cbpfr-four-gate-closeout-2026-10-12`  
**Scope:** Re-analysis of the archived 18-run OpenMC C5G7 study; no new transport simulation is initiated by this report.

## Decision

**Do not launch another OpenMC campaign yet.** First complete the analysis, software integration, and evidence presentation using the archived statepoints and run records. The existing experiment is sufficient for a defensible exploratory analysis of repeatability and for validating data-processing/software behavior. It is not sufficient to certify physical acceptability or to claim that CB-PFR improves physical decisions.

A further simulation is justified only if a named scientific question cannot be resolved from existing evidence—for example, a documented missing tally, a predeclared source-convergence sensitivity study, or a controlled comparison after the physical acceptance rule and candidate mapping have been reviewed.

## Existing dataset integrity

The archived run-level table contains 18 rows: six layouts (`MMUU`, `MUMU`, `MUUM`, `UMMU`, `UMUM`, `UUMM`) and three independent seed rounds (820000, 830000, 840000). Every layout has three records; seed IDs and statepoint hashes are unique; the MGXS hash is common across the study. The recorded settings are 7,000 batches, 500 inactive batches, 10,000 particles per batch, and two threads.

These checks establish record structure and provenance consistency, not model correctness or physical validation.

## Descriptive results

| Layout | Mean k-effective | Between-seed SD, k-effective | Mean relative fission-rate peaking proxy | Between-seed SD, proxy |
|---|---:|---:|---:|---:|
| MMUU | 1.1436721 | 0.0000506 | 1.2953689 | 0.0006666 |
| MUMU | 1.1437002 | 0.0000968 | 1.2963641 | 0.0010560 |
| MUUM | 1.1562627 | 0.0000861 | 1.3161492 | 0.0012969 |
| UMMU | 1.1864986 | 0.0001396 | 1.8671004 | 0.0015410 |
| UMUM | 1.2046883 | 0.0000585 | 1.8167194 | 0.0001908 |
| UUMM | 1.2046416 | 0.0001025 | 1.8160915 | 0.0008942 |

The proxy is defined for this study as the maximum of the four assembly-integrated fission tallies divided by their mean. A lower value means less relative peaking under this definition only. It is not absolute power, a licensed safety metric, or a complete reactor objective.

Between-seed variation and within-run Monte Carlo uncertainty are different quantities. With only three seed rounds per layout, any across-seed confidence interval is descriptive and fragile; it must not be represented as a convergence certificate.

## What CB-PFR can responsibly do now

1. Preserve optimizer feasibility as a separate status from physical-evidence status.
2. Carry the raw measurements, tally definition, uncertainty fields, source diagnostics, and provenance into an auditable candidate record.
3. Evaluate an explicit, reviewed acceptance rule only when one is supplied.
4. Return `UNKNOWN` / `NO_SELECTION` if acceptance criteria, model validation, or convergence evidence are unresolved.
5. Compare the CB-PFR decision rule with simple baselines using the same candidate set, data, and evaluation budget.
6. Export the decision, rationale, evidence references, and limitations—not just a rank.

## Why another simulation is not the immediate next step

The central open issue is not the number of Monte Carlo histories alone. The research still needs a defensible mapping between the optimizer's candidate encoding and the C5G7 UO2/MOX configurations, a physically justified acceptance rule for the intended question, and independent review of the model/tally/convergence evidence. More runs with an unresolved mapping or no defensible decision criterion would add compute cost without resolving the core claim.

## Gates before any future confirmatory run

A new simulation should be scheduled only after all applicable items below are recorded:

- [ ] Candidate encoding and material/layout mapping reviewed and frozen.
- [ ] Target physical quantity and tally normalization documented.
- [ ] Acceptance limits and their scientific source documented before looking at confirmatory outcomes.
- [ ] Source-convergence and inactive-batch sensitivity criteria predeclared.
- [ ] Baselines, decision metrics, uncertainty treatment, and practical-effect threshold frozen.
- [ ] Existing raw data and statepoints checked for whether they can already answer the question.
- [ ] Confirmatory run count and compute budget justified by a specific unresolved hypothesis.

## Claim boundary

Supported: the archived high-budget OpenMC jobs produced a reproducible, structured set of results for six modeled layouts, and those results can support exploratory comparison and software/data-pipeline testing.

Not yet supported: that any layout is physically acceptable; that the model is independently validated; that convergence is certified; or that CB-PFR has demonstrated a confirmatory improvement in physical feasibility or reliability.

## Software design requirement

The UI must visually distinguish **optimization status**, **evidence integrity**, **model/convergence status**, and **physical acceptance status**. It must never convert a successful workflow, valid file hash, low proxy, or preflight pass into a physical pass. A missing or unreviewed acceptance rule must result in `UNKNOWN`, and the application must block a final winner claim.
