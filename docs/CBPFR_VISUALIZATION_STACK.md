# CB-PFR visualization stack policy

**Scope:** HTML scientific workstation, including web/index.html, web/app.js, web/styles.css, and OpenMC-derived geometry/field evidence.

Official documentation: [Plotly.js](https://plotly.com/javascript/) · [VTK.js](https://kitware.github.io/vtk-js/).

## Chosen stack

| Visual task | Renderer | Why this is the current choice |
|---|---|---|
| Candidate point/range plots, distributions, scatter plots, mesh heatmaps, contour/profile views, 2-D terrain, and recorded axial volume | **Plotly.js 2.35.2** | One quantitative-chart engine keeps axes, hover data, numeric colorscales, responsive sizing, and uncertainty presentation consistent. |
| Exact 3 × 3 core and 17 × 17 pin-lattice source map | **Native SVG** | The map is derived from the checked-in OpenMC XML-derived geometry manifest, can be inspected sharply at any zoom, and needs no separate 3-D engine. |
| Optional interactive, extruded core geometry with orbit/zoom/click inspection | **Existing Three.js 0.180.0 module** | This is retained because the workstation already has a distinct 3-D core-inspection feature. It is not the renderer for numeric scalar fields, and the source SVG map remains the fallback if the module/WebGL is unavailable. |
| A potential future VTK.js viewer | **Not installed** | Do not introduce VTK.js solely to restyle a Plotly surface or duplicate the current recorded volume view. Revisit only for a demonstrated requirement such as advanced volume clipping, transfer functions, or larger datasets that Plotly cannot serve adequately. |

No new npm package or Python runtime dependency is added by this stage.

## Installed recorded axial evidence

The workstation branch includes the audited production UMMU field files at `evidence/cbpfr_axial_3d/`. The primary payload is `axial_tally_3d.npz`, sourced from [successful OpenMC production run 38393987067](https://github.com/thenextw4ng/cb-pfr/actions/runs/38393987067), accompanied by its statepoint summary, input audit, input manifest, and provenance record.

The current recorded run uses 7,000 batches (500 inactive), 10,000 particles per batch, and 6,500 active realizations. It exports 51 × 51 × 30 = 78,030 bins for flux, fission, and nu-fission. NPZ byte count and SHA-256 are recorded in both source summary and provenance, checked before publication, and rechecked by the local API before values are served. A focused workstation-smoke test checks this metadata and the returned array dimensions.

This evidence makes the viewer available in this branch without requiring a local download from Actions. The lazy, hash-verified artifact installer remains a recovery path if the files are absent in a local checkout; it accepts only a successful high-budget UMMU production artifact, not the small smoke-profile result.

## Loading and fallback behavior

- Plotly is version-pinned at the HTML entry point and has a second CDN source. If both fail, the workstation records the load failure and each chart shows a bounded, readable engine-unavailable message.
- Three.js is imported as an optional ES module. Failure is surfaced as renderer status; the existing SVG source map remains usable.
- The compact renderer strip in the HTML reads actual browser/module state. “VTK.js · NOT LOADED BY DESIGN” describes the deliberate absence of that optional dependency; it is not a claim that VTK.js was probed and found broken.

## Scientific rendering rules

- A numeric colorscale (for example Cividis) encodes a numeric value only. Material categories remain a separate channel: MOX uses amber, UO₂ uses cyan/blue, reflectors use neutral grey.
- Exactly four assembly-proxy values stay as four discrete positions. No contour, smoothing, or interpolation is generated from those four observations.
- The 51 × 51 planar OpenMC mesh and the 51 × 51 × 30 axial tally remain separate source datasets. A 3-D volume only renders when the real axial export and sidecar metadata are installed; the 2-D field is not substituted as a volume.
- The axial volume and assembly-integrated proxy remain source-scale/exploratory records, not absolute power or safety outputs unless the source explicitly establishes their units and normalisation.

## Revisit VTK.js only when

1. There is a concrete user task requiring capabilities not supported by the existing Plotly volume/isosurface or SVG geometry view.
2. A representative, real OpenMC dataset is available.
3. An integration prototype demonstrates the gain in interaction, memory, responsiveness, and maintainability.
4. Bundle size, browser support, provenance, and regression tests are documented before adopting it.

This is an intentionally small stack: one main quantitative plot engine, source-derived native SVG for precise 2-D geometry, and the already-existing optional Three.js core viewport.
