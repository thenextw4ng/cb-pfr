# CB-PFR Stage 4 — Physical Axial 3-D Model and Mesh Tally

## Purpose

Stage 4 promotes the archived C5G7 axial geometry builder to an auditable OpenMC 3-D transport input and creates a true volumetric mesh tally. The existing Stage 3 Plotly surface is a 2-D field plotted as a height surface; it is not this result.

## What is reused

The screening artifact c5g7-study-640000 contains six candidate source trees and a model/3d/build-xml-3d.py file for each. The builder describes a 3 x 3 x 10 assembly lattice with 21.42 cm axial pitch over z = -107.1 to +107.1 cm. The archive's actual completed statepoints are from model/2d/statepoint.5000.h5; it does not contain recorded 3-D transport statepoints.

The prepared model therefore reuses the archived geometry/material/lattice source and its multi-group cross-section generation, but no 3-D outcome is inferred from the 2-D statepoint.

## Stage 4 implementation

- scripts/prepare_c5g7_axial_3d.py safely extracts the exact archived source package, validates the expected source anchors, redirects the 3-D builder to a dedicated tally module, and exposes batch/particle/seed controls as environment variables.
- The generated model/tally_3d.py writes a regular mesh with 51 x 51 x 30 bins covering [-32.13, 32.13] cm in X/Y and [-107.1, 107.1] cm in Z. Each mesh bin is 1.26 x 1.26 x 7.14 cm. There are 78,030 spatial bins and three scores: flux, fission, and nu-fission.
- A 21.42 cm axial lattice layer contains three tally bins in Z, so the volumetric tally can resolve axial variation in the stored source geometry.
- scripts/audit_c5g7_axial_3d.py checks generated XML inputs and exports a compressed [z, y, x, score] volume plus an audit summary from the actual statepoint. Uncertainty is derived from OpenMC's stored tally sum/sum-of-squares and realization count.
- A GitHub Actions workflow performs the structural audit and a small transport smoke run on the canonical UMMU candidate. A smoke run checks the 3-D pipeline works; it does not establish convergence or benchmark acceptance.

## Axial geometry cross-check against the published benchmark

The official OECD/NEA C5G7 MOX benchmark specification describes each fuel assembly as 21.42 cm × 21.42 cm × 192.78 cm, with an additional 21.42 cm water reflector above the fuel assemblies; the overall 3-D quarter-core domain is 64.26 cm × 64.26 cm × 214.20 cm, with a reflected lower-Z boundary and vacuum upper-Z boundary. See [OECD/NEA, NEA/NSC/DOC(2003)16, Chapter 2](https://www.oecd-nea.org/upload/docs/application/pdf/2019-12/nsc-doc2003-16.pdf), pp. 13–14.

The archived builder's 10-layer stack maps to those dimensions: nine 21.42 cm layers contain the repeated fuel-bearing 3 × 3 cross section (192.78 cm total), and its tenth/top layer is the 21.42 cm all-water reflector. The source also uses a 17 × 17 pin lattice with 1.26 cm pitch and 0.54 cm pin/guide-tube radius, consistent with the same specification. The generated XML audit now checks the actual candidate-specific universe map, all nine repeated layers, the all-reflector top layer, material IDs/names, pin/assembly pitches, and axial boundary locations/conditions.

This is a source-geometry consistency result—not proof that computed values match benchmark references. Numerical validation still requires a statistically credible 3-D transport result and comparison of eigenvalue and normalized pin/assembly fission-power estimates against the published reference; this workflow's 3-D mesh fission tally is source-normalized rather than absolute power.

## Workstation integration

The HTML workstation now includes a separate **Physical axial 3D tally volume** panel. It reads `/api/axial-3d`, which serves only the NPZ exported from a real multi-layer OpenMC statepoint. The existing Stage 3 surface remains labelled as a surface representation of a 2-D tally and is not used as fallback data.

For local use, place both `axial_tally_3d.npz` and `AXIAL_3D_STATEPOINT_SUMMARY.json` in `evidence/cbpfr_axial_3d/` under the repository root, or set `CBPFR_AXIAL_TALLY_NPZ` to the NPZ file path before starting `web_server.py`. The browser UI provides a 3-D volumetric trace plus a selectable physical Z slice, tally-score selector, mean/relative-error colouring, opacity, and palette controls. The volume uses log10(mean) for visual contrast by default while hover readouts retain the recorded untransformed mean and uncertainties.

The panel deliberately shows an unavailable state when no 3-D NPZ is installed; it does not inflate or recycle the 2-D tally. The artifact's `AXIAL_3D_STATEPOINT_SUMMARY.json` records the originating statepoint SHA-256 and the NPZ summary has its own SHA-256, allowing source/output matching during installation.

## Outputs and evidence

A successful workflow uploads the prepared XML files, input manifest, actual statepoint and summary, plus:
- axial_tally_3d.npz: per-bin mean, standard error, relative error, score names, and physical X/Y/Z cell-center coordinates;
- AXIAL_3D_STATEPOINT_SUMMARY.json: statepoint/input hashes, dimensions, scores, realization count, uncertainty method, and score-level descriptive metrics.

Each file hash is retained so a later workstation integration can bind the 3-D visualization to exact source inputs and calculation outputs.

## Claim boundary

A smoke statepoint establishes only that the selected run completed and emitted a 3-D mesh tally. It does not prove statistical convergence, benchmark agreement, best fuel loading, a quantum advantage, absolute power normalization, reactor safety, burnup/depletion, or thermal-hydraulic behavior. The UI must not substitute the Stage 3 pseudo-height field for this data.
