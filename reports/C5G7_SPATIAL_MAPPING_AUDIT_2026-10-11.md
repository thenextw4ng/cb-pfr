# Independent C5G7 spatial-mapping audit — 2026-10-11

## Result

**Status: STRUCTURAL_MAPPING_CHECK_PASS; PHYSICAL_VALIDATION_NOT_ESTABLISHED.**

An independent audit was run against the downloaded artifact from [corrected-group smoke workflow 38104812849](https://github.com/thenextw4ng/cb-pfr/actions/runs/38104812849), using the raw HDF5 statepoint contents and the generated `build-xml-2d.py` for each candidate. It did not use OpenMC's Python API to reshape the tally data.

- Three rounds × six candidates = 18 cases inspected.
- All 18 candidate IDs matched their UO₂/MOX layout signature.
- All 18 generated 3×3 core lattice assignments matched the recorded layout and the top-down row/left-to-right column convention.
- All 18 tally mesh definitions had dimensions 51×51×1, XY bounds −32.13 to +32.13 cm, and 1.26 cm bin pitch.
- For all 18 raw statepoints, fission tally support was present in each of the four expected 17×17 fuel-assembly blocks.
- All four fuel blocks had equal positive-bin counts; the right reflector column and bottom reflector row had zero positive fission bins.
- The HDF5 mesh result array was independently reshaped with Fortran order because the serialized mesh-bin sequence increments x fastest. This agrees with the expected core support pattern.

The smoke artifact itself has SHA-256 `16ab7ac4b19dac6e757662ee6acf5e6fc0f295ff8734e718bc6e15c8d71bab65`.

## Reproduction

With the ZIP artifact downloaded and unpacked into `study-root/`, and with Python, NumPy, and h5py installed:

```bash
python scripts/audit_c5g7_spatial_mapping.py \
  --study-root study-root \
  --out spatial_mapping_audit.json
```

The C5G7 repeated-seed smoke workflow now includes this audit step so future workflow artifacts preserve the machine-readable result. The script checks the generated lattice assignment against each case manifest, mesh dimensions/bounds/pitch, raw HDF5 tally shape, fission support in each fuel block, and zero fission support in the fixed reflector regions.

## Interpretation boundary

This result improves confidence that the reported assembly-integrated fission-rate proxy slices the mesh into the intended four fuel blocks for these generated inputs. It does **not** validate the cross-section library, prove benchmark identity, establish convergence, propagate tally covariance, convert fission tallies to absolute power, or establish a physically acceptable layout. The corrected-group runs remain smoke-budget (100 batches, 10 inactive, 1,000 particles per batch). No candidate winner is declared.
