# Stage 4 — Assembly-integrated fission-rate proxy map

## Spatial convention

The source CSV exposes exactly four assembly-integrated proxy fields: **p00_fission_rate**, **p01_fission_rate**, **p10_fission_rate**, and **p11_fission_rate**. The workstation maps them row-major to the same position convention used by the source-derived core geometry:

| Map row | Geometry coordinate | Source field | Display position |
|---|---|---|---|
| Top row | row 0, column 0 | p00_fission_rate | P00 |
| Top row | row 0, column 1 | p01_fission_rate | P01 |
| Bottom row | row 1, column 0 | p10_fission_rate | P10 |
| Bottom row | row 1, column 1 | p11_fission_rate | P11 |

This is a discrete four-observation display. It is not a contour, interpolation, pin map, or replacement for the separate 51 × 51 OpenMC mesh tally.

## Quantitative colour versus material category

- Cell fill uses one sequential Cividis scale for recorded proxy values.
- The displayed range is global across the exact candidate/signature-matched records and remains the same when the selected candidate changes.
- The selected-candidate map is the only view with a visible colourbar; the six-candidate matrix reuses the range without duplicating it.
- Material category appears only as the tile outline and in the material key: MOX = amber, UO₂ = cyan. The 3 × 3 core geometry keeps reflector material in neutral grey.
- A white outline identifies the currently selected spatial position. Clicking a tile or the position buttons synchronizes the position detail panel.

## Values, missing data, and units

Values are joined using both **candidate_id** and **layout_signature**, never borrowed from a different candidate. The tile and detail controls display the recorded CSV values. If one position is absent/non-finite, it is shown as unavailable (—) rather than converted to zero or reconstructed; the other available positions remain inspectable.

The archived CSV names the fields as fission-rate proxies but does not document a physical unit or absolute-power normalisation. Accordingly, the colourbar labels the scale as a *fission-rate proxy* and expressly states that its CSV unit is not documented. No unit or absolute-power claim is invented.

## Provenance treatment

The expanded provenance is behind a closed-by-default disclosure so the visual map remains the primary object. It retains source CSV identity, record-level hashes, seed information, and uncertainty/interpretation notes. Proxy-run seeds are distinct from candidate-summary seeds; the views are descriptive, not paired statistical comparisons.

## Regression checks

The browser smoke test checks that all six candidate identities select correctly, the four map values exactly match the source API in P00/P01/P10/P11 order, tile material names track each candidate signature, the geometry row/column mapping is stated, the quantitative scale matches the candidate matrix, only one colourbar is enabled, and tile/button selection remains synchronized. It also confirms the visual remains a heatmap, not a continuous contour.
