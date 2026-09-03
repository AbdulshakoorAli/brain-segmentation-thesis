# Afterthought-1 interactive 3D professor-demo report

## Milestone decision

The single-record Extra-18 Afterthought-1 native-space professor demo passes its scoped technical validation and is ready for local professor review.

The displayed DKT31 labels and derived surfaces are **manual reference segmentations, not model predictions**. This is a research visualization, not a clinical viewer, anatomical-validity claim, or model result. Phase 1A is not claimed complete.

Dataset splitting remains explicitly deferred. No 70/15/16 targets, cohort matrix, seed, tie-breaking rule, or modeling coordinate-space policy was approved or used. No split, preprocessing, training, inference, evaluation, or other-record mesh artifact was created.

## Selected accepted pair

- Canonical pair: `MB101:Extra-18:Afterthought-1:native:brain-DKT31`
- Cohort / participant / space: Extra-18 / Afterthought-1 / native
- Shape: `176 x 256 x 256`
- Spacing: `0.999997139 x 1 x 1 mm`
- Orientation: `LAS`
- Foreground labels: 62 original DKT IDs, 31 left and 31 right
- Nonzero manual-label voxels represented: 434,509

The existing read-only loader revalidates NIfTI parsing, shape, affine, spacing, orientation, finite MRI/label values, MRI content, integer/nonempty labels, dictionary vocabulary, manifest metadata, subject identity, and native-space naming before the app displays anything.

## Implementation

### Derived meshes

`src/brain_segmentation/mesh_visualization.py` generates one surface per observed foreground DKT ID. A one-voxel zero border closes labels that touch an array boundary; marching cubes uses level 0.5 on each unmodified categorical mask, and vertices are mapped through the accepted NIfTI affine into world millimetres.

- Exact derived surfaces: Lewiner marching cubes, `step_size=1`; 608,797 vertices and 1,237,714 faces.
- Coherent interactive display surfaces: the same algorithm at `step_size=2`; 137,214 vertices and 293,476 faces.
- Mesh regions: 62/62; background: transparent and not meshed.
- Stored under `data/derived/visualization/afterthought1_native_dkt31_meshes/`: 249 files, 27,416,571 bytes.
- Original DKT IDs, distributed names, hemispheres, deterministic colors, source voxel counts, hashes, algorithms, affine, and pair identity are recorded in `mesh_manifest.json`.

The step-2 surfaces are derived display geometry for browser responsiveness; the full step-1 surfaces remain the primary derived mesh artifact. Neither path changes MRI intensities or DKT values.

### Streamlit application

`apps/afterthought1_3d_professor_demo.py` provides:

- browser-native Plotly orbit rotation, scroll/modebar zoom, and hover;
- independent left/right hemisphere controls;
- selection of all, none, or individual regions by original DKT ID and anatomical name;
- deterministic colors matching the accepted 2D viewer;
- 3D surface-opacity control;
- accepted axial, coronal, and sagittal MRI/manual-label views beside the 3D view;
- MRI-only, label-only, and overlay modes;
- independent anatomical slice sliders and 2D overlay-opacity control;
- visible pair identity, cohort, native space, shape, spacing, orientation, and region table;
- prominent manual-reference/not-prediction and non-clinical notices;
- recoverable load errors displayed inside the app.

The app uses the accepted loader and orientation/slice functions without rewriting the existing 2D viewer.

## Dependency changes

`requirements-visualization.txt` adds only the direct packages required by this milestone:

- `streamlit==1.62.0` — local browser application and headless app testing;
- `plotly==7.0.0` — interactive 3D surface rotation, zoom, and hover;
- `scikit-image==0.26.0` — deterministic marching-cubes surface extraction.

Existing NumPy, NiBabel, Pytest, and Matplotlib pins were retained. Transitive packages were installed only inside `.venv`.

## Validation

### Passed

- Accepted real-pair loader validation: all established essential checks passed.
- Mesh coverage: all 62 observed foreground IDs and all 434,509 foreground voxels are represented; 0 unknown IDs and 0 background surface.
- Mesh integrity: finite `N x 3` vertices, valid triangular faces, in-range indices, manifest counts, original-ID/name/hemisphere/color mapping, and native-affine world coordinates passed for every region.
- 3D behavior: 62 all-region traces, 31 left traces, 31 right traces, orbit drag mode, scroll zoom, hover ID/name text, opacity, and region filtering passed.
- Accepted 2D behavior: axial/coronal/sagittal rendering passed in MRI-only, label-only, and overlay modes using center slices 159/121/89.
- Streamlit interaction test: initial 62-region display; both 31-region hemisphere states; individual region selection; surface/overlay opacity; all three slice controls; label-only mode; and the manual-reference notice passed with 0 app exceptions.
- Local server: hidden Streamlit process returned HTTP 200 with `ok` from `/_stcore/health` and was stopped after validation.
- Windows launcher: validation mode returned code 0 and the expected Streamlit command.
- Regression: existing tests passed 8/8.
- Determinism: repeat full generation produced 255 byte-identical mesh, screenshot, and validation files.
- Preservation: selected raw NIfTI hashes matched before/after; accepted manifests, dictionaries, QC artifacts, lineage/grouping artifacts, raw archives, loader, and 2D visualization code remained unchanged.

### Failed

- None.

### Skipped

- Meshes for the other 201 canonical rows; dataset splits; preprocessing; training; inference; quantitative evaluation; clinical validation; and model-result visualization.

### Unverified

- Professor usability and presentation quality on the target classroom display/GPU/browser.
- Scientific or anatomical validity beyond faithful display of the accepted distributed manual label volume.
- Previously recorded package-version, licensing, NKI acquisition, OASIS overlap, and historical label-notice uncertainties.

### Blocked

- Phase 1A completion and subsequent scientific-design decisions remain subject to human review.

## Screenshots

- [Combined 3D and accepted 2D preview](screenshots/afterthought1_3d_professor_demo/afterthought1_professor_demo_combined.png)
- [All 62 DKT regions](screenshots/afterthought1_3d_professor_demo/afterthought1_3d_all_regions.png)
- [Left hemisphere](screenshots/afterthought1_3d_professor_demo/afterthought1_3d_left_hemisphere.png)
- [Right hemisphere](screenshots/afterthought1_3d_professor_demo/afterthought1_3d_right_hemisphere.png)
- [Accepted orthogonal 2D views](screenshots/afterthought1_3d_professor_demo/afterthought1_accepted_2d_views.png)

## Launch

Double-click `launch_afterthought1_3d_demo.cmd` in the repository root, or run:

```powershell
.\launch_afterthought1_3d_demo.cmd
```

Direct equivalent:

```powershell
.\.venv\Scripts\python.exe -m streamlit run apps\afterthought1_3d_professor_demo.py
```

The launcher checks that the project virtual environment and app exist, opens the local Streamlit application, and leaves the terminal available for clean shutdown with `Ctrl+C`.

## Remaining limitation and next action

This MVP intentionally supports only Afterthought-1 native space. It renders categorical cortical surfaces without a 3D MRI volume, and browser responsiveness uses coherent step-2 display meshes while retaining the full step-1 artifacts. The known near-midline source-support appearance remains visible in the accepted sagittal view and is not repaired.

The exact next action is professor review of the local demo using the one-click launcher, followed by recorded visualization feedback. Split-policy approval must not be requested during this milestone.
