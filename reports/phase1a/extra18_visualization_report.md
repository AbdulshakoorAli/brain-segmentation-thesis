# Extra-18 visualization pre-MVP report

## Milestone decision

The Extra-18 visualization pre-MVP passes this scoped milestone. It loads and displays one deterministically selected, verified native-space MRI/manual-DKT31 pair without changing, resampling, normalizing, reorienting, cropping, padding, or remapping the source data.

The displayed DKT31 volume is a **manual reference segmentation, not a model prediction**.

## Deterministic selection

Selection rule: choose the minimum `(canonical_pair_id, scan_id)` among included rows in `mindboggle101_scan_manifest.csv` where cohort is `Extra-18`, space is `native`, and pairing/validation statuses are `verified`.

- Canonical pair: `MB101:Extra-18:Afterthought-1:native:brain-DKT31`
- Scan: `Extra-18:Afterthought-1:native`
- Participant: `Afterthought-1`
- Participant group: `Mindboggle-Afterthought-1`
- Source subject/participant identifier: `Satrajit Ghosh`
- Cohort/space: `Extra-18` / `native`
- MRI: `data/raw/mindboggle101/extracted/Extra-18/Extra-18_volumes/Afterthought-1/t1weighted_brain.nii.gz`
- Manual DKT31: `data/raw/mindboggle101/extracted/Extra-18/Extra-18_volumes/Afterthought-1/labels.DKT31.manual.nii.gz`

## Observed metadata

- MRI/label shape: `176 × 256 × 256`
- MRI/label spacing: `0.9999971389770508, 1.0, 1.0 mm`
- MRI/label orientation: `LAS`
- MRI affine:

  ```text
  [-0.997238397598, -0.039569918066,  0.062802039087,   89.876663208008]
  [-0.032958760858,  0.994133114815,  0.103019535542, -107.860748291016]
  [ 0.066509865224, -0.100665450096,  0.992694735527, -121.274826049805]
  [ 0,                 0,                 0,                1]
  ```

- Label affine differs only at MRI/label translation element `[0,3]`: maximum absolute difference `7.62939453125e-06`, accepted using existing `rtol=1e-5`, `atol=1e-5`.
- Observed IDs: background `0` plus `1002;1003;1005;1006;1007;1008;1009;1010;1011;1012;1013;1014;1015;1016;1017;1018;1019;1020;1021;1022;1023;1024;1025;1026;1027;1028;1029;1030;1031;1034;1035;2002;2003;2005;2006;2007;2008;2009;2010;2011;2012;2013;2014;2015;2016;2017;2018;2019;2020;2021;2022;2023;2024;2025;2026;2027;2028;2029;2030;2031;2034;2035`.
- Unknown observed label IDs: none.
- Initial voxel slices: sagittal `89`, coronal `121`, axial `159`, computed as the integer center of the nonzero segmentation bounding extent.

The full machine-readable affine, label-ID, checksum, and validation evidence is in `data/derived/qc/extra18_visualization_validation.json`.

## Implementation

- `src/brain_segmentation/loading.py` selects a verified manifest record and returns read-only MRI/label arrays, both affines, spacing, orientation, original label IDs/names, manifest metadata, and validation outcomes.
- The loader rejects missing/unparseable files, non-3D or mismatched shapes, affine/spacing/orientation mismatches, non-finite or constant MRI values, non-integer/empty labels, unknown IDs, manifest disagreement, subject mismatch, and non-native products.
- `src/brain_segmentation/visualization.py` is separate from loading. It renders axial, coronal, and sagittal voxel planes with anatomical edge labels and deterministic display-only colors for original DKT IDs.
- `scripts/run_extra18_visualization.py` performs deterministic selection, real-pair validation, screenshot generation, widget checks, and before/after raw-file hashing. Use `--show` to open the interactive viewer on a graphical workstation.

No transform or source-file write exists in the loading or visualization path. The label-index array used by Matplotlib is display-only; stored DKT values are not remapped or rewritten.

## Visualization features and validation

Passed:

- both NIfTIs exist and parse;
- both volumes are 3D with matching accepted shape;
- affines match at the accepted QC tolerance;
- spacing and LAS orientation match each other and the manifest;
- MRI is finite, nonempty, and nonconstant (`0` to `281` in accepted QC);
- labels are finite, integer-valued, nonempty, and dictionary-complete;
- MRI and labels are the same Extra-18 participant and native product;
- axial, coronal, sagittal, and combined views render successfully;
- MRI-only, label-only, and overlay modes respond;
- all three slice sliders and the opacity slider respond;
- background label color is transparent and all 62 foreground IDs have deterministic distinct colors;
- clicking a displayed plane reports the original label ID and dictionary region name;
- anatomical labels, subject/cohort/space/shape/spacing/slice metadata, and the manual-reference notice are visible;
- visual inspection found the three overlays aligned with the accepted MRI anatomy;
- existing QC regression tests passed `8/8` once;
- two final rendering runs produced byte-identical screenshots and validation JSON.

Failed: none.

## Dependencies

`requirements-visualization.txt` is new. It reuses `requirements-qc.txt` and adds only `matplotlib==3.10.7`. Installation in the project `.venv` also installed Matplotlib's standard transitive packages: contourpy `1.3.3`, cycler `0.12.1`, fonttools `4.63.0`, kiwisolver `1.5.1`, Pillow `12.3.0`, pyparsing `3.3.2`, python-dateutil `2.9.0.post0`, and six `1.17.0`. No preprocessing or medical-imaging transform dependency was added.

## Screenshots

- `reports/phase1a/screenshots/extra18_visualization/afterthought1_native_axial_overlay.png`
- `reports/phase1a/screenshots/extra18_visualization/afterthought1_native_coronal_overlay.png`
- `reports/phase1a/screenshots/extra18_visualization/afterthought1_native_sagittal_overlay.png`
- `reports/phase1a/screenshots/extra18_visualization/afterthought1_native_three_plane_overlay.png`

## Preservation and limitations

Selected MRI and label SHA-256 values matched before and after rendering. All previously accepted manifests, QC/lineage/overlap artifacts, dictionaries, reports, research logs, shared QC code, and raw archives retained their established hashes.

This pre-MVP validates one native Extra-18 pair only. It is a 2D orthogonal voxel viewer, not a clinical viewer, preprocessing pipeline, 3D surface reconstruction, or model-evaluation tool. It makes no medical-validity claim. Licensing, Dataverse-v2/OSF-v3 equivalence, NKI acquisition uncertainty, OASIS external overlap, and historical label-notice scope remain unresolved.

## Next recommended task

Human-review the four screenshots, orientation convention, controls, and dependency choice. If accepted, extend the same manifest-driven viewer to allow selection among other already verified records without adding preprocessing, inference, or dataset splits.
