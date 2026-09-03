# Mindboggle-101 focused visual acceptance report

## Milestone decision

The manifest-driven viewer passes this focused human visual-acceptance milestone. The reported Afterthought-1 sagittal appearance is explained by the unmodified distributed skull-stripped MRI/manual-DKT31 pair, not by a visualization-axis or orientation defect. No viewer-code correction was justified.

The displayed DKT31 volumes are **manual reference segmentations, not model predictions**. This acceptance concerns display consistency only; it is not a clinical or anatomical-validity claim.

## Afterthought-1 sagittal investigation

- Canonical pair: `MB101:Extra-18:Afterthought-1:native:brain-DKT31`
- Shape: `176 x 256 x 256`
- Spacing: `0.999997139 x 1 x 1 mm`
- Orientation: `LAS`
- Investigated sagittal slices: `84`, `87`, `89`, `91`, and `94`

The original arrays were loaded read-only. For sagittal slice 89, both arrays use voxel axis 0, index 89, `transpose(1, 0)`, no rotation, no explicit flip, `origin="lower"`, identical `[-0.5, 255.5, -0.5, 255.5]` extents, aspect ratio 1.0, and nearest-neighbor display. The displayed MRI and label-index arrays exactly equal the independently derived expected slices and share the same plotting transform.

### Source-array measurements

| Measurement | Full volume | Sagittal slice 89 |
|---|---:|---:|
| Nonzero MRI voxels | 1,157,182 | 6,040 |
| Nonzero label voxels | 434,509 | 1,720 |
| Label voxels where MRI is exactly zero | 0 | 0 |
| Percentage of labels where MRI is zero | 0.0% | 0.0% |

The full-volume MRI nonzero bounding box is `[23, 41, 58]` through `[155, 202, 216]`, inclusive; the label bounding box is `[23, 41, 102]` through `[155, 202, 216]`. In the displayed sagittal slice, the MRI bounding box is `[58, 42]` through `[206, 198]` and the label bounding box is `[112, 42]` through `[206, 198]`.

At all 1,720 labeled voxels in slice 89, source MRI intensity is nonzero. Its minimum/median/maximum at those voxels is `49/106/201` on the unchanged full-volume display range `0–281`; zero label voxels fall at or below 1% or 5% of that range. Therefore, intensity windowing is not hiding faint MRI support beneath the apparently detached labels.

The source label mask at slice 89 contains 64 four-connected components. Nearby slices contain 16, 24, 64, 27, and 15 components at slices 84, 87, 89, 91, and 94 respectively, and each has zero label voxels on zero MRI. The appearance is strongest at the selected near-midline slice and is visibly present in the original MRI-only and label-only arrays before overlay composition.

### Cause classification

- Visualization-axis/orientation bug: **no**.
- MRI windowing hiding faint tissue: **no**.
- Distributed source-pair property: **yes**. The skull-stripped MRI support itself is disconnected in this near-midline voxel slice, and the manual labels occupy corresponding nonzero MRI voxels.
- Unresolved cause: **no for the reported display phenomenon**. Broader anatomical or scientific validity remains outside this display acceptance.

The source arrays were not shifted, resampled, reoriented, cropped, filtered, rewritten, or repaired. Because the display transformations are identical, no accepted visualization code or original screenshot was changed as a bug fix.

## Focused usability evidence

The required three deterministic records were reviewed:

| Category | Canonical pair | Space / orientation | Selected axial, coronal, sagittal slices | Shape / spacing | Review |
|---|---|---|---|---|---|
| Afterthought-1 native LAS | `MB101:Extra-18:Afterthought-1:native:brain-DKT31` | native / LAS | 159, 121, 89 | `176x256x256` / `0.999997139,1,1` | Spatially consistent with source support; disclose near-midline fragmentation. |
| Deterministic non-LAS native | `MB101:Extra-18:Colin27-1:native:brain-DKT31` | native / RAS | 88, 109, 90 | `181x217x181` / `1,1,1` | Spatially consistent; distributed native MRI visibly includes extra-cranial signal outside the cortical label scope. |
| Deterministic LAS MNI152 | `MB101:Extra-18:Afterthought-1:MNI152:brain-DKT31` | MNI152 / LAS | 87, 111, 89 | `182x218x182` / `1,1,1` | Spatially consistent with source support; near-midline fragmentation is not a transform mismatch. |

Practical checks passed for cohort filtering (observed counts `36/42/44/40/40`), participant/scan selection, coordinate-space selection, canonical-pair updates, all three slice controls, opacity affecting only label overlay, MRI-only/label-only/overlay modes, deterministic colors and transparent background, dictionary label lookup, recoverable invalid-ID handling, and visibility of the manual-reference/not-prediction notice.

## Created evidence

- Machine-readable acceptance record: `data/derived/qc/mindboggle101_visual_acceptance.json`
- Reproducible focused runner: `scripts/run_mindboggle101_visual_acceptance.py`
- Diagnostic screenshots:
  - [MRI only](screenshots/visual_acceptance/afterthought1_native_sagittal89_mri_only.png)
  - [Label only](screenshots/visual_acceptance/afterthought1_native_sagittal89_label_only.png)
  - [Overlay](screenshots/visual_acceptance/afterthought1_native_sagittal89_overlay.png)
  - [Nearby slices 84/87/89/91/94](screenshots/visual_acceptance/afterthought1_native_sagittal_84_87_89_91_94_overlays.png)
- Combined usability screenshots:
  - [Afterthought-1 native LAS](screenshots/visual_acceptance/afterthought1_native_las_combined.png)
  - [Colin27-1 native RAS](screenshots/visual_acceptance/colin27_1_native_ras_combined.png)
  - [Afterthought-1 MNI152 LAS](screenshots/visual_acceptance/afterthought1_mni152_las_combined.png)

No dependency was added or changed. The selected NIfTI checksums matched before and after generation. The final preservation audit also covers the accepted source code, raw archives, manifests, dictionaries, QC, lineage, participant-group, report, log, and screenshot baselines.

## Accounting

- Passed: identical transformations; quantitative source-support explanation; three focused visual reviews; selector, control, lookup, notice, and recoverable-error checks; source preservation.
- Failed: none.
- Skipped: the other 199 visual records, extensive new tests, splits, preprocessing, training, inference, evaluation, and 3D reconstruction.
- Unverified: visual alignment of the remaining 199 records and usability on untested GUI/backend/DPI configurations.
- Blocked: licensing reconciliation and formal phase-transition decisions remain human-review items.

## Known limitations and next milestone

The viewer faithfully exposes source-product heterogeneity, including fragmented near-midline skull-stripped support and native volumes with extra-cranial signal. It does not repair or adjudicate those scientific properties. The exact historical label-notice scope and established provenance uncertainties remain documented.

The exact next recommended thesis milestone is a human scientific-design review of a conservative participant-grouped split policy, including all repeat/counterpart constraints and unresolved overlap cautions. Only after approval should a separate deterministic split-generation milestone begin.
