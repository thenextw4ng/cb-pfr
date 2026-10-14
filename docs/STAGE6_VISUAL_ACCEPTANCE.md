# Stage 6 — Scientific visual acceptance

## Goal

Stage 6 provides an automated review gate for the scientific HTML workstation on a separate branch. The gate checks that displayed values and coordinates trace to the repository evidence, and saves browser screenshots plus a structured report. It does not merge code into the default branch and does not certify reactor physics.

## Acceptance criteria

| Area | Automated acceptance rule |
|---|---|
| Core geometry | Six candidate signatures match the OpenMC-derived manifest; 2 MOX + 2 UO₂ fuel locations are row-major P00, P01, P10, P11; the five reflector sites are invariant; pin dimensions and source hashes are present. When `CBPFR_TEST_ARCHIVE` is supplied, re-compute the archive SHA-256 and all six candidates’ raw `geometry.xml` and `materials.xml` SHA-256 values against the manifest. |
| Candidate charts | Six unique candidate records load and preserve their recorded uncertainty/descriptive interpretation. The k-effective display is not treated as a physical-feasibility ranking. |
| Assembly proxy | The view shows four discrete source values, checks exact candidate ID plus layout identity, shares one Cividis numeric scale, keeps MOX/UO₂ colors on separate material outlines, highlights the selected position, and does not interpolate a 2×2 contour. |
| Spatial fields | Heatmap, contour, central-row profile and terrain use the same recorded 51×51 source mesh and coordinate vectors. Per-cell display values, source hover mean/Monte Carlo SE/relative SE and coordinates are compared directly. Playwright drags and resets the 3D surface camera and changes vertical exaggeration, while asserting that display controls do not alter source-derived Z values or hover payloads. Missing/non-positive source cells must remain missing rather than becoming artificial peaks. |
| Axial volume | The viewer must load the recorded multi-layer 51×51×30 OpenMC tally, display the Plotly volume trace, and expose its statepoint/NPZ hashes, batch budget, active realizations and relative-error summary. It cannot substitute the 2D terrain. |
| Desktop/mobile | Playwright opens 1440-pixel desktop and 390-pixel mobile viewports; checks document and chart bounds plus panel-heading/control overflow at both sizes; and saves screenshots. |
| Provenance | Repository hashes, candidate/run identities, uncertainty scope and non-claims remain accessible in the HTML and source sidecars. |

## Reproduce locally

Run source/data checks:

    python tests/test_visual_acceptance.py

To enable the strict raw-source XML cross-check locally, set `CBPFR_TEST_ARCHIVE=/path/to/c5g7-study-640000.zip` before running the Python test. The Stage 6 GitHub Actions gate provides this archive automatically and fails if the full archive or any candidate XML hash differs from the committed manifest.
    node --check web/app.js
    node --check tests/browser_visual_acceptance.cjs

The browser test additionally requires Python packages numpy and h5py, Node.js, Playwright and Chromium. Start the server with an archive that contains the recorded 2D mesh statepoint, for example:

    export CBPFR_STATEPOINT_ARCHIVE="$HOME/path/to/c5g7-study-640000.zip"
    export CBPFR_STATEPOINT_MEMBER="c5g7-2x2-UMMU/model/2d/statepoint.5000.h5"
    export CBPFR_STATEPOINT_BASELINE="/tmp/no-authoritative-baseline.json"
    python web_server.py

Then in a second terminal:

    npm install --no-save playwright@1.56.0
    npx playwright install chromium
    node tests/browser_visual_acceptance.cjs

The GitHub Actions job downloads and hash-checks the recorded study ZIP, validates the archived geometry/material XML hashes for all six candidates against the source manifest, runs the Python source/data tests, starts the HTML server, runs Playwright, and uploads an artifact containing screenshots, server logs, and JSON acceptance results. The mesh API’s `hash_matches` value is independently checked: a missing same-run baseline must remain `DATA LOADED · HASH NOT CHECKED`, never be promoted to “verified.”

## Scientific limits that must remain explicit

- The assembly fission-proxy CSV reports exploratory smoke results. Its absolute unit is not documented, the values are not absolute power, and proxy seeds are independent of the candidate-summary seeds. They must not be described as paired data or converted into a fabricated continuous field.
- The 2D OpenMC spatial section uses a separate 51×51×1 statepoint mesh. It is distinct from the four assembly-integrated proxy values.
- The archived 3D tally is a real exported 51×51×30 statepoint with 7,000 batches, 500 inactive batches and 6,500 active realizations. The summary reports bin-wise uncertainty. This is not by itself benchmark acceptance or physical validation.
- The 3D input audit documents inherited assumptions: nine repeated cross-sectional lattice layers plus an all-reflector top layer, a reflective bottom Z boundary and a vacuum top Z boundary. Those assumptions need independent reactor-physics review before benchmark or design claims.
- A hash match establishes data identity, not physics validity. Low relative error addresses tally sampling uncertainty, not adequacy of the physical model, nuclear data, boundary conditions, depletion, power normalization or thermal hydraulics.

## Status policy

Do not call Stage 6 passed until the workflow is green and its saved JSON/screenshot artifact has been inspected. If the browser gate finds a real defect, fix it on this branch and rerun the complete gate before requesting merge.
