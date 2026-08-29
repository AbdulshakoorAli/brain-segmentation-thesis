# Research log: Phase 1A Extra-18 visualization pre-MVP

- Date: 2026-08-30
- Skill: repository-local `brain-segmentation-research`.
- Initiating request: move directly from the accepted global manifest checkpoint to a narrowly scoped Extra-18 visualization pre-MVP with only the minimum read-only loading required for one verified native pair.
- Intended deliverables: reusable loader and separate visualization logic, essential scientific validation, axial/coronal/sagittal overlays with controls, four representative screenshots, report, research log, and project-state update.
- Boundaries: no splits, preprocessing, source rewrite, resampling, normalization, reorientation, crop/pad, label remapping, training, inference, model evaluation, or surface reconstruction.

## Evidence and implementation

- Deterministic selection from the global manifest chose `MB101:Extra-18:Afterthought-1:native:brain-DKT31` / `Extra-18:Afterthought-1:native` by minimum `(canonical_pair_id, scan_id)`.
- MRI and manual DKT31 paths are same-subject native products for `Afterthought-1`.
- Real-pair observations: shape `176×256×256`, spacing `0.9999971389770508/1/1 mm`, LAS orientation, affine maximum absolute difference `7.62939453125e-06`, and 62 known foreground DKT IDs plus background.
- Initial sagittal/coronal/axial slices `89/121/159` were derived from the nonzero segmentation extent, not appearance.
- Added `src/brain_segmentation/loading.py`, `src/brain_segmentation/visualization.py`, and `scripts/run_extra18_visualization.py`.
- Added only Matplotlib `3.10.7` as a direct dependency through `requirements-visualization.txt`; existing NumPy/NiBabel requirements are reused.

## Validation result

- Loader checks: 23/23 passed on the selected raw pair.
- Rendering/control checks: 9/9 passed, including three planes, three display modes, slice/opacity controls, transparent background, deterministic foreground colors, and label ID/name display.
- Existing QC regression suite: 8/8 passed once.
- Visual inspection: all four screenshots are legible; orientation labels and metadata are visible; overlays follow accepted cortical anatomy.
- Determinism: two final renders produced byte-identical four screenshots and validation JSON.
- Preservation: selected raw MRI/label hashes, all accepted artifacts, raw archives, dictionary, and shared QC implementation remained unchanged.
- Failed: 0.
- Skipped: all other subjects/cohorts, extensive synthetic loader tests, splits, preprocessing, training, inference, quantitative model evaluation, and 3D reconstruction.
- Unverified: clinical/scientific interpretation beyond technical display; unresolved dataset provenance and external-overlap items are unchanged.
- Blocked: licensing reconciliation remains a human-review requirement but does not block local technical review of this pre-MVP.

## Outcome

The Extra-18 visualization pre-MVP passes its scoped milestone and is ready for human review. The displayed DKT31 volume is a manual reference segmentation, not a model prediction.
