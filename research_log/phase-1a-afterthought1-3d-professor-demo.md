# Research log: Afterthought-1 interactive 3D professor demo

- Date: 2026-08-31
- Skill: repository-local `brain-segmentation-research`.
- Initiating request: reject and defer the proposed split policy, then build only a local Streamlit professor-demo MVP for the accepted Extra-18 Afterthought-1 native MRI/manual-DKT31 pair.
- Intended deliverables: read-only real-pair loading, derived per-region meshes, interactive 3D and accepted 2D views, hemisphere/region controls, deterministic original-ID colors, Windows one-click launcher, screenshots, validation evidence, report, and project-state update.
- Boundaries: no split files, preprocessing, training, inference, quantitative evaluation, raw-data modification, all-record mesh generation, clinical claims, or Phase 1A completion claim.

## Initiating decision

The user explicitly did not approve the proposed split policy. The 70/15/16 targets, cohort matrix, seed, tie-breaking method, and coordinate-space decision are deferred until after professor review of the visualization. Split approval must not be requested again during this milestone.

## Validation result

### Implementation evidence

- Reused the accepted read-only loader and 2D orientation/slice helpers without changing them.
- Added `src/brain_segmentation/mesh_visualization.py` for original-ID per-region mesh derivation, Plotly figures, and accepted orthogonal rendering.
- Added `apps/afterthought1_3d_professor_demo.py`, focused build/validation scripts, and `launch_afterthought1_3d_demo.cmd`.
- Added direct pins for Streamlit 1.62.0, Plotly 7.0.0, and scikit-image 0.26.0; all installations were confined to `.venv`.
- Generated meshes only for `MB101:Extra-18:Afterthought-1:native:brain-DKT31` and saved them outside raw data.

### Observed validation

- The accepted pair passed all established read-only loader checks; shape `176x256x256`, spacing `0.999997139,1,1`, orientation `LAS`.
- Meshed 62/62 observed foreground IDs: 31 left, 31 right, 434,509 source label voxels, 608,797 exact vertices, and 1,237,714 exact faces.
- Generated coherent step-2 display surfaces with 137,214 vertices and 293,476 faces; background was not meshed.
- Plotly orbit rotation, scroll zoom, hover ID/name, hemisphere filtering, region filtering, and opacity configuration passed.
- MRI-only, label-only, and overlay modes rendered all three accepted planes at initial slices 159/121/89.
- Streamlit AppTest exercised both hemisphere states, individual region selection, both opacity sliders, all slice sliders, display mode, and notice visibility with zero app exceptions.
- A real hidden Streamlit server returned HTTP 200 / `ok`; the one-click launcher validation returned code 0.
- Existing tests passed 8/8. Repeat generation produced 255 byte-identical files.
- Selected raw MRI/label hashes matched before and after. No split file or other-record mesh directory was created.

### Accounting

- Passed: real-pair validation, mesh coverage/integrity, 3D and 2D rendering, controls, app test, local server, launcher, regression, determinism, and preservation.
- Failed: none.
- Skipped: all other records, splits, preprocessing, model work, evaluation, and clinical validation.
- Unverified: professor experience on the target display/browser/GPU and scientific validity beyond source-faithful rendering.
- Blocked: Phase 1A completion and later scientific-design decisions remain human-review items.

The scoped Afterthought-1 3D professor-demo MVP passes technical validation and is ready for local professor review. It does not complete Phase 1A.
