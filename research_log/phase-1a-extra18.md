# Phase 1A Extra-18 Archive Processing Log

## Initiation

- Date: 2026-08-23
- Phase: 1A — Dataset foundation
- Milestone scope: verify, safely extract, inventory, and pair only `Extra-18_volumes.tar.gz`; do not perform full NIfTI voxel-level quality control or process another cohort.
- Skill: `brain-segmentation-research` (repository-local; no explicit version declared)
- Intended deliverable: `data/derived/manifests/extra18_scan_inventory.csv`, an exact extracted-tree record, archive and pairing validation evidence, and an updated `PROJECT_STATE.md`.

## Initiating prompt

> Use `$brain-segmentation-research`.
>
> Continue Phase 1A from the current `PROJECT_STATE.md` and process only `data/raw/mindboggle101/archives/volumes/Extra-18_volumes.tar.gz`.
>
> Verify its checksum and gzip/tar integrity, reject unsafe member paths, extract safely to `data/raw/mindboggle101/extracted/Extra-18/`, record the exact structure, classify all subject NIfTI files and coordinate spaces, identify same-subject/same-space MRI-label pairs, compare subject IDs with supplied metadata, create `data/derived/manifests/extra18_scan_inventory.csv`, preserve raw files, keep licensing and version-equivalence issues unresolved, update project state and the research log, and state readiness for header and voxel-level QC.

## Observed inputs

- Archive: `data/raw/mindboggle101/archives/volumes/Extra-18_volumes.tar.gz`
- Existing inventory row: 732,012,448 bytes; SHA-256 `89e5d9a635fb12227e3c132d33ecb15aeeaeb54a7db02ad29ecfa7085468eb9c`.
- Extraction target was absent before this task: `data/raw/mindboggle101/extracted/Extra-18/`.
- Supplied comparison metadata: `subject_list_Mindboggle101.txt` and `subject_sources_Mindboggle101.txt`.

## Archive validation and extraction

- Recomputed SHA-256: `89e5d9a635fb12227e3c132d33ecb15aeeaeb54a7db02ad29ecfa7085468eb9c` — exact inventory match.
- Gzip stream was consumed through EOF without decompression or checksum error.
- Independent `tar -tzf` listing completed successfully.
- Archive contains 183 members under the sole top-level path `Extra-18_volumes/`.
- Unsafe path count: 0. Checks covered `/`-rooted paths, UNC/rooted paths, drive-letter paths, and path components equal to `..` after slash normalization.
- Symlink, hard-link, device, and other non-regular/non-directory entry count: 0.
- The previously absent target directory was created, then the archive was extracted without overwrite. The distributed top-level directory name was preserved.
- Extracted archive members exactly match disk paths: 0 missing from disk and 0 unexpected disk paths.
- Exact structure record: `data/derived/manifests/extra18_extracted_structure.txt`, containing all 183 extracted entries (19 directories and 164 files) as repository-relative paths, with byte sizes for files.

## Subjects and file classification

Extracted subjects (18):

`Afterthought-1`, `Colin27-1`, `HLN-12-1`, `HLN-12-10`, `HLN-12-11`, `HLN-12-12`, `HLN-12-2`, `HLN-12-3`, `HLN-12-4`, `HLN-12-5`, `HLN-12-6`, `HLN-12-7`, `HLN-12-8`, `HLN-12-9`, `MMRR-3T7T-2-1`, `MMRR-3T7T-2-2`, `Twins-2-1`, `Twins-2-2`.

Each subject directory has the same nine observed files:

- Native T1-weighted MRI: `t1weighted.nii.gz`.
- Native skull-stripped T1: `t1weighted_brain.nii.gz`.
- Native manual DKT31 cortical label: `labels.DKT31.manual.nii.gz`.
- Native combined DKT31/manual-plus-aseg label derivative: `labels.DKT31.manual+aseg.nii.gz`.
- MNI152 T1-weighted MRI: `t1weighted.MNI152.nii.gz`.
- MNI152 skull-stripped T1: `t1weighted_brain.MNI152.nii.gz`.
- MNI152 manual DKT31 cortical label: `labels.DKT31.manual.MNI152.nii.gz`.
- MNI152 combined DKT31/manual-plus-aseg label derivative: `labels.DKT31.manual+aseg.MNI152.nii.gz`.
- MNI152 ancillary affine text file: `t1weighted_brain.MNI152.affine.txt`.

Counts:

- Extracted files: 164.
- NIfTI files: 144 — 72 native and 72 MNI152.
- Non-skull-stripped T1 NIfTIs: 36 — 18 native and 18 MNI152.
- Skull-stripped T1 NIfTIs: 36 — 18 native and 18 MNI152.
- Manual DKT31 cortical label NIfTIs: 36 — 18 native and 18 MNI152.
- Combined manual DKT31-plus-aseg NIfTIs: 36 — 18 native and 18 MNI152; recorded as additional label derivatives, not selected as canonical labels.
- Other unclassified NIfTIs: 0.
- Expected ancillary affine text files: 18.
- Unexpected files: `Extra-18_volumes/.DS_Store` and `Extra-18_volumes/._.DS_Store`; neither is a NIfTI or subject file.

## Metadata comparison

- All 18 extracted subject IDs occur exactly in `subject_list_Mindboggle101.txt`: 0 unmatched extracted IDs.
- All 18 extracted subject IDs have a row and source value in `subject_sources_Mindboggle101.txt`: 0 missing source rows.
- Manifest `participant_id` records the supplied Mindboggle-101 subject ID. Manifest `source_subject_id` records the supplied `Source` field verbatim. No demographic values were copied or inferred.
- This comparison verifies identifier presence only; it does not resolve acquisition lineage beyond the supplied source field.

## Pairing and manifest

- Artifact: `data/derived/manifests/extra18_scan_inventory.csv`.
- Rows: 36, with the exact 10 requested columns and repository-relative MRI/label paths.
- Canonical candidate rule: prefer `t1weighted_brain` with `labels.DKT31.manual`, as directed by the repository skill, and match only within the same subject directory and filename-declared coordinate space.
- Native matched candidates: 18.
- MNI152 matched candidates: 18.
- Missing or ambiguous canonical candidates: 0.
- Full-head T1 and `manual+aseg` files are named in each row's notes as same-space alternatives and are not counted as additional canonical pairs.
- Every row is marked `matched_pending_nifti_qc`, not scientifically accepted as a usable pair, because NIfTI parsing, shape, affine, orientation, spacing, finite-value, vocabulary, and overlap checks were outside this task.
- Manifest validation: 36 unique `scan_id` values, 0 absolute paths, 0 missing referenced files, 0 absent source IDs, and 0 native/MNI152 filename-space mismatches.

## Validation result

### Passed

- Archive checksum matched the existing inventory.
- Gzip decompression integrity and tar parsing/listing passed.
- All archive member paths passed absolute/traversal checks; no link or special entries were present.
- Extraction completed into the requested previously absent target without overwriting existing raw files.
- The 183 archive members and extracted disk paths match exactly.
- All 18 subject IDs matched both supplied metadata sources.
- All 36 canonical MRI-label candidates match subject and filename-declared coordinate space; native and MNI152 paths are not mixed.
- Required manifest schema, row uniqueness, relative-path resolution, and referenced-file existence checks passed.

### Failed

- None.

### Skipped

- NIfTI parsing and header checks: dimensions, affine matrices, orientation, and voxel spacing.
- Voxel-level checks: finite values, MRI content/intensity variation, label integrality and vocabulary, nonempty segmentation, spatial overlap, and duplicate-content analysis.
- Full quality control, other cohorts, data splits, loaders, training code, and visualization.

### Unverified

- The 36 structure- and space-matched candidates are not yet verified usable MRI-label pairs until header and voxel-level checks pass.
- `native` and `MNI152` classifications are based on distributed filenames and directory structure; NIfTI transforms have not been inspected.
- Harvard Dataverse v2 versus OSF/project v3 equivalence remains unresolved.

### Blocked

- Package/component licensing reconciliation remains unresolved and requires human review.
- No archive-processing blocker remains for Extra-18's next technical QC task.

## Raw-data preservation

- The source archive was read only and retains the inventory-matching checksum.
- No pre-existing raw file was modified, moved, renamed, deleted, or overwritten.
- The only raw-tree writes were newly extracted archive members under the explicitly requested, previously absent `data/raw/mindboggle101/extracted/Extra-18/` target.

## Readiness and exact next recommended task

Extra-18 is ready to begin NIfTI header and voxel-level quality control, but it is not yet QC-passed or ready for inclusion in a training dataset.

Exact next recommended task: process only the 36 canonical Extra-18 candidate pairs in `extra18_scan_inventory.csv`; parse every NIfTI, then record image/label shape, affine compatibility, orientation, spacing, finite values, MRI nonemptiness and intensity variation, label integrality and IDs, segmentation nonemptiness, spatial brain overlap, and duplicate/repeat evidence, without resampling or modifying raw files.
