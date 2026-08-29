# Research log: manifest-driven Mindboggle-101 viewer

- Date: 2026-08-30
- Skill: repository-local `brain-segmentation-research`.
- Initiating request: accept the Extra-18 visualization pre-MVP and extend it into a manifest-driven viewer for all 202 verified native/MNI152 canonical pairs.
- Intended deliverables: minimal loader/viewer reuse, general selector runner, exactly 10 real-record smoke validations, report, research log, and project-state update.
- Boundaries: no source modification, transforms, splits, preprocessing, training, inference, quantitative evaluation, 3D reconstruction, or medical claims.

## Implementation evidence

- Inspected the accepted loader, viewer, Extra-18 runner, 202-row global manifest, DKT dictionary, environment, and project state before editing.
- Added stable manifest catalog loading and `canonical_pair_id` lookup to the existing loader.
- Generalized essential validation from native-only to verified native and MNI152 products without weakening affine, spacing, orientation, finite-value, content, or vocabulary checks.
- Replaced fixed voxel-axis plane assumptions with orientation-derived anatomical plane axes. No source array is reoriented.
- Preserved the existing Extra-18 runner and added `scripts/run_mindboggle101_viewer.py` for cascading cohort/participant/space/pair selectors, direct canonical launch, recoverable errors, and smoke validation.
- Added no dependency; existing Matplotlib and standard-library Tk are reused.

## Validation result

- Manifest catalog: 202 verified records, 202 unique canonical IDs, cohort counts 36/42/44/40/40.
- Smoke selection: exactly one deterministic native and MNI152 record from each of five observed cohorts.
- Smoke outcome: 10 loaded, 10 passed essential checks, 10 rendered axial/coronal/sagittal planes, 0 failed, 0 screenshots.
- Native variation represented: LAS, RPS, and ASL orientations plus 170×256×256, 176×256×256, 192×256×256, and 256×256×160 shapes; MNI152 records were 182×218×182 LAS.
- All six orientation codes present in the 202-row manifest passed anatomical-axis mapping.
- Invalid canonical lookup produced a clear error and exit code `2` instead of an unhandled crash.
- Existing QC tests passed 8/8 once.
- The 20 selected NIfTI hashes matched before and after; all 47 preservation-baseline artifacts remained unchanged.

## Accounting and outcome

- Passed: manifest lookup, selectors, both spaces, essential validation, three-plane rendering, controls, orientation mapping, error handling, regression tests, and preservation.
- Failed: none.
- Skipped: exhaustive 202-record rendering, additional screenshots, extensive synthetic tests, splits, preprocessing, model work, evaluation, and surfaces.
- Unverified: human DPI/backend usability and all previously recorded provenance/scientific uncertainties.
- Blocked: licensing and formal phase transition remain human-review items.

The manifest-driven Mindboggle-101 viewer passes this scoped technical milestone and is ready for local human research use. Labels remain manual DKT31 references, not predictions.
