# Research log: focused Mindboggle-101 visual acceptance

- Date: 2026-08-30
- Skill: repository-local `brain-segmentation-research`.
- Initiating request: investigate the Afterthought-1 native sagittal-slice-89 appearance, review exactly three orientation/space categories, exercise focused viewer usability, preserve accepted artifacts, and decide visual acceptance from evidence.
- Boundaries: no source transforms or rewrites, splits, preprocessing, training, inference, evaluation, surface reconstruction, extensive test expansion, or clinical claim.

## Procedure

1. Re-read repository instructions, the skill Phase 1A references, project state, accepted loader/viewer/runners, global manifest, DKT dictionary, and accepted reports.
2. Captured SHA-256 preservation baselines for accepted code, raw archives, manifests, QC/lineage/overlap artifacts, dictionaries, prior visualization evidence, and the selected source NIfTIs.
3. Loaded `MB101:Extra-18:Afterthought-1:native:brain-DKT31` read-only and independently checked the viewer's sagittal voxel selection, transpose, rotation, flip, origin, extent, aspect, and interpolation for MRI and label.
4. Measured volume and slice-89 nonzero support, zero-MRI label overlap, bounding boxes, label-supported intensity distributions, and slice-mask connected components; repeated slice measurements at 84, 87, 89, 91, and 94.
5. Generated MRI-only, label-only, overlay, and nearby-slice diagnostics.
6. Deterministically selected Afterthought-1 native LAS, the minimum verified non-LAS native record (Colin27-1 RAS), and the minimum verified LAS MNI152 record (Afterthought-1); generated one combined view for each.
7. Exercised selectors, pair updates, per-plane sliders, opacity, modes, colors/transparency, dictionary lookup, invalid-ID recovery, and notice visibility.

## Observed evidence

- MRI and label use voxel axis 0, index 89, `transpose(1,0)`, no rotation or explicit flip, `origin=lower`, matching extents, aspect 1.0, and the same axes transformation.
- Full volume: 1,157,182 nonzero MRI voxels; 434,509 nonzero label voxels; 0 labels on exactly zero MRI (0.0%).
- Slice 89: 6,040 nonzero MRI voxels; 1,720 nonzero label voxels; 0 labels on exactly zero MRI (0.0%).
- At slice-89 labels, MRI minimum/median/maximum is 49/106/201 on the unchanged 0–281 range; none lie below the 1% or 5% thresholds used only to investigate display visibility.
- Slice-89 label support contains 64 four-connected components in the original slice. Nearby component counts are 16, 24, 64, 27, and 15 for slices 84, 87, 89, 91, and 94.
- The MRI-only diagnostic visibly contains corresponding disconnected source support; label-only and overlay views preserve it in the same locations.
- All focused selector and control checks passed. An invalid canonical ID raised a recoverable `ValueError` rather than terminating the viewer process.

## Outcome

The sagittal appearance is a property of the distributed skull-stripped MRI/manual-DKT31 pair at a near-midline voxel slice. It is not caused by different MRI/label display operations and not explained by faint MRI support hidden by windowing. No visualization correction was made.

- Passed: source-array explanation, transform identity, three-record focused review, controls/selectors, error recovery, notice, and preservation.
- Failed: none.
- Skipped: 199 other visual records and all out-of-scope dataset/model work.
- Unverified: remaining-record visual alignment and untested GUI/backend environments.
- Blocked: licensing and phase-transition approval remain human responsibilities.

The manifest viewer passes focused human visual acceptance with the documented source-display limitation. The next recommended milestone is human review and approval of a conservative participant-grouped split design; no split was created here.
