# Phase 1A: Dataset foundation

## Objective

Build a reproducible, inspected dataset foundation before visualization or model training. Phase 1A prepares data; it does not train a model or implement the 3D viewer.

## Milestones

Complete milestones in this order unless the project state records an approved reason to change it.

### 1. Source and scope record

- Record dataset title, dataset version, retrieval date, authoritative URL/DOI, package name, and local raw-data location.
- Capture the license notice shipped with each downloaded component.
- State which components are in scope: individual T1 MRI volumes and corresponding manual DKT cortical labels.
- Record that templates and population atlases are optional for Phase 1A.

### 2. Dataset inventory

Create a machine-readable manifest with one row per scan. Include at least:

- `scan_id`
- `participant_id` or best available grouping identifier
- `cohort`
- `source_subject_id`, when documented
- `mri_path`
- `label_path`
- `space` (`native`, `MNI152`, or verified alternative)
- image and label dimensions
- image and label voxel spacing
- image and label orientation
- affine-match result
- label IDs present
- validation status and exclusion reason

Use relative paths where practical. Do not include undocumented age, sex, diagnosis, or participant identity.

### 3. Data dictionary

Create two dictionaries:

1. A manifest dictionary defining every manifest field, type, allowed values, source, and missing-value rule.
2. A label dictionary mapping stored DKT label IDs to region names, hemisphere, and training class index if remapping is later approved.

Generate the label dictionary from the distributed label-definition file or another authoritative Mindboggle source. Preserve original IDs. Do not assume the IDs are contiguous.

### 4. Quality control

For every intended MRI/label pair, check:

- both files can be decompressed and parsed as NIfTI;
- dimensions and affine matrices are compatible;
- orientations and voxel spacings are recorded;
- values are finite;
- MRI is nonempty and has plausible intensity variation;
- label volume is integer-valued in meaning, even if stored as floating point;
- label IDs occur in the data dictionary;
- segmentation is nonempty and spatially overlaps the brain;
- duplicates and repeat acquisitions are identified.

Write a summary report and a machine-readable table of failures. Never modify raw files to make a check pass.

### 5. Leakage-safe splits

Create train, validation, and test assignment files only after grouping information is available.

- Group repeat scans from the same participant together.
- Consider cohort and acquisition-source balance where group counts allow it.
- Use a fixed recorded seed and deterministic algorithm.
- A 70/15/16 scan target may be used as an initial goal for 101 scans, but participant grouping takes precedence over exact counts.
- Preserve a frozen test set and do not use it for model or preprocessing decisions.
- Emit a split audit proving there is no participant/group overlap.

Do not create random scan-level splits when participant lineage is unresolved.

### 6. Data-loader contract

Specify and implement a loader only after the actual package structure is inspected. Its minimum output contract is:

```text
image: numeric 3D array or tensor
label: matching 3D array or tensor
scan_id: stable string
affine: 4 x 4 transform
spacing: three physical voxel sizes
metadata: cohort, participant grouping, source paths, space
```

The loader must fail clearly on missing pairs, incompatible shapes/affines, unknown required labels, or corrupted files. Keep normalization, resampling, cropping, patch sampling, and augmentation as explicit configurable transforms rather than hidden behavior.

## Required deliverables

- Dataset source and license record
- Scan manifest
- Manifest data dictionary
- DKT label dictionary
- Quality-control report and failure table
- Deterministic train/validation/test assignments
- Split-leakage audit
- Tested loader plus a minimal loader test
- Updated `PROJECT_STATE.md`
- Prompt and validation log entries

## Phase acceptance criteria

Phase 1A passes only when:

1. Every included scan has one verified MRI/label pair.
2. Every included label ID is documented.
3. No unresolved affine, orientation, or shape mismatch remains in included data.
4. Exclusions are explicit and reproducible.
5. No participant/group occurs in more than one split.
6. Re-running split generation with the same inputs and seed produces identical assignments.
7. The loader successfully reads representative samples from every cohort and split.
8. A reviewer can trace every derived artifact to the original dataset version and code/configuration.

If raw data are not yet available, complete only the source record, proposed schemas, and acquisition plan; mark file-dependent checks as blocked rather than passed.
