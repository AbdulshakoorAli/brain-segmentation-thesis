# Phase 1A Extra-18 NIfTI QC Research Log

## Initiation

- Date: 2026-08-26
- Phase: 1A — Dataset foundation
- Skill: `brain-segmentation-research` (repository-local; no explicit version declared)
- Intended deliverable: reusable NIfTI pair QC/tests; pair QC, failures, DKT dictionary, updated Extra-18 manifest, report, and state update.
- Boundary: only 36 canonical Extra-18 pairs; `manual+aseg` auxiliary; no other cohorts, splits, loader, training, or visualization.

## Initiating prompt

The user requested header and voxel-level QC for 18 native and 18 MNI152 Extra-18 MRI/manual-DKT31 pairs, including parsing, geometry, affine tolerance, orientation, spacing, space consistency, finite/content checks, label integrality/vocabulary, segmentation overlap, and exact file/voxel duplicates. Reusable code, specified synthetic tests, two test/QC runs, determinism confirmation, artifact/state/log updates, and a checkpoint decision were required. Licensing and version equivalence were to remain unresolved.

## Inputs and decisions

- Manifest: `data/derived/manifests/extra18_scan_inventory.csv`, exactly 36 unique Extra-18 rows and 18 per space.
- Only `t1weighted_brain[.MNI152].nii.gz` and `labels.DKT31.manual[.MNI152].nii.gz` are canonical.
- Labels parsed from the distributed `label_definitions.txt` `cortex_numbers_names` block: 62 unique cortical IDs. Original IDs preserved; class indices blank.
- Voxel `0` is background, not an invented anatomical dictionary row.
- Affine/spacing comparison: `rtol=1e-5`, `atol=1e-5`.
- Technical overlap: nonzero segmentation support intersecting finite, nonzero skull-stripped MRI support; no clinical threshold.

## Implementation

- Added `src/brain_segmentation/qc.py`, `scripts/run_extra18_qc.py`, `tests/test_qc.py`, and `requirements-qc.txt`.
- Runner enforces cohort/count/canonical-name boundaries and rejects `manual+aseg` targets.
- Tests cover valid input, shape mismatch, affine mismatch, non-finite MRI and label values, non-integer labels, empty segmentation, and unknown IDs.
- Repository-local ignored `.venv`: NumPy 2.5.2, NiBabel 5.4.2, pytest 9.1.1.

## Validation

- Test run 1: 8/8 passed in 0.83 seconds.
- QC run 1: 36 verified, 0 failed, 0 blocked; 62 dictionary rows; 0 failure rows.
- Test run 2: 8/8 passed in 0.67 seconds.
- QC run 2: 36 verified, 0 failed, 0 blocked; 62 dictionary rows; 0 failure rows.
- Byte-identical CSV hashes across QC runs:
  - Pair QC: `c7bee67f1226753b2683ebdd5c5222a000d7f5e982ebe09d9272722ae38ca3f5`.
  - Failures: `6439a730c7d63f2a588757b7d5a55cb244ef879745f17709022ec0399d7dbda7`.
  - Dictionary: `76a113acec22cad1ec1fcb67fedc7f2b3d6a8eafe6e53ca6c5873e8a64651306`.
  - Manifest: `f6018f27e385cb803f4e56239a0d4ca4ed60df8c08d6b7045984363f8db1def7`.
- Maximum affine elementwise absolute difference: `7.62939453125e-06`.
- Segmentation overlap fraction range: `0.999974524511` to `1.0`.
- Unknown anatomical label IDs: none. Exact file/voxel/pair duplicates: none.
- Subjects requiring technical-QC investigation: none.
- Post-QC source archive checksum exactly matched the prior inventory.

## Passed

- 36/36 pairs; 18 native and 18 MNI152. Extra-18 passes this scoped technical checkpoint.

## Failed

- None.

## Skipped

- Auxiliary files, other cohorts, splits, loader, training, and visualization.

## Unverified

- Dataverse v2/OSF v3 equivalence, lineage beyond supplied metadata, independent MNI provenance, and scientific/clinical validity.

## Blocked

- Licensing reconciliation and broader Phase 1A completion remain pending human review/future milestones.

## Next recommendation

Human-review this checkpoint and unresolved provenance/licensing notes, then explicitly scope the next single Phase 1A cohort inventory/QC task. Do not create splits until lineage is known.

