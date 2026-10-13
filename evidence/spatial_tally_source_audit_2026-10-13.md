# Spatial tally source audit — 2026-10-13

## Outcome

**A recoverable spatial-data source was found. No new OpenMC simulation was run for this audit.**

The GitHub Actions artifact c5g7-study-640000 contains six completed C5G7 2×2 candidate statepoints with linked 51×51 2-D mesh tallies and score bins flux, fission, and nu-fission. Every included statepoint hash matches the corresponding CASE_RESULT.json output hash.

## Source archive identity

- GitHub Actions workflow run: 38182056526
- Artifact ID: 11719691969
- Artifact name: c5g7-study-640000
- Archive SHA-256: 7a5e2a3daf87d0141ddc5e0922b88c4c0e2c3cb91af67ca6a2f50b6535e9862b
- Recovered candidate statepoints: 6
- Unique statepoint hashes: 6
- Per-case statepoint byte hashes verified against CASE_RESULT.json: yes

## Recovered statepoint inventory

| Candidate | Seed | Batches | Inactive | Active tally realizations | Statepoint SHA-256 |
|---|---:|---:|---:|---:|---|
| c5g7-2x2-MUMU | 640002 | 5000 | 500 | 4500 | 5d8318c51580af7b7f6a3ca8c01b3e9e2847e3591845b91a44441111b8dee6f6 |
| c5g7-2x2-MMUU | 640001 | 5000 | 500 | 4500 | d81eea61163aad3a689e4128631c0bb686086c74e5d296c652a26bca06637175 |
| c5g7-2x2-MUUM | 640003 | 5000 | 500 | 4500 | fae2b64f2ae4c39690165423862e40dbfa851fd89cd12fa79dbe01a42639754d |
| c5g7-2x2-UMMU | 640000 | 5000 | 500 | 4500 | 41b0169545ef709662775fe3e47b477dafc79b8a32ad0b501024e3f9bf11281c |
| c5g7-2x2-UUMM | 640005 | 5000 | 500 | 4500 | 171fa545375dce9663feacac64d04ae27d2bd9ece27a61978006cd7a5c681b6a |
| c5g7-2x2-UMUM | 640004 | 5000 | 500 | 4500 | 830a55876ef8587601c4086d85783d28aef2f4a877df8b35b6b0c33244fb6dd2 |

## HDF5 tally structure

- OpenMC version reported by the source statepoints: 0.16.0
- Mesh dimensions linked to tally 1: 51 × 51 × 1 (2-D mesh)
- Tally results shape: 2601 × 3 × 2 (2601 mesh bins × three scores × accumulated sum/sum-of-squares)
- Score bins: flux, fission, nu-fission
- Tally 1 references mesh filter 1; the filter type is mesh and its bins dataset contains mesh ID 1.
- The statepoint stores accumulated tally sum and sum-of-squares. Mean and standard error can be derived using the per-tally count of 4500 active realizations. The audit confirmed finite derived values for all six candidates.

## Root cause found in the current reader

1. read_mesh_evidence() checks filter groups for datasets named mesh or mesh_id.
2. The audited OpenMC 0.16 statepoints store the mesh ID in the mesh filter's bins dataset ([1]). The parser leaves the mesh ID unset.
3. Because a mesh filter is present but cannot be associated with mesh 1, the parser rejects the valid 51×51 tally and raises “No compatible 2-D OpenMC mesh tally was found”. This matches the message in the workstation screenshot.
4. The front-end Plotly functions for spatial heatmap, contour, central-row profile, and 3-D surface still exist. They are blank because the mesh API cannot return the tally data.

## Plot-file inventory

- plots.xml configurations: 6
- Rendered PNG/JPG/WEBP/PPM/TIFF images in this artifact: 0
- Rendered VTK/VTI/VTP/VTU/VTM/XDMF files in this artifact: 0
- The artifact contains plot configuration files and model-building code, but not the rendered plot images or VTK-family outputs. The dashboard's Plotly 3-D surface is a surface representation of the 2-D mesh tally, not a true volumetric 3-D transport result.

## Scientific boundary

The recovered runs use 5,000 batches, 5,000 particles per batch and 500 inactive batches (4,500 active tally realizations). The source study explicitly states that independent validation remains necessary and that its settings are smoke-test settings—not benchmark-grade or convergence-certified results. The recovered statepoints are an audited fallback for restoring plotting behavior and regression testing, not a substitute for validated production results.

The user's separate local archive, OpenMC_HDF5_Evidence_2026-10-11.zip, was not available for direct byte-level inspection in this audit. Its local hash and HDF5 metadata should be recorded separately; do not silently equate it with this GitHub Actions artifact.

## Next implementation step

Update mesh-filter parsing to read mesh IDs from the bins dataset, validate referenced mesh dimensions against tally bin count, and test against both this recovered artifact and the user's separate local production archive. The next stage should then require /api/mesh to succeed in browser CI when spatial visualizations are required; an allowed HTTP 503 must no longer count as a pass.
