# Research log: Phase 1A NKI-TRT-20 QC, lineage, and overlap

- Date: 2026-08-27
- Skill: repository-local `brain-segmentation-research`.
- Scope: only NKI-TRT-20 archive validation/extraction, inventory, unchanged NIfTI QC, lineage, label issues, and NKI cross-cohort overlap.

## Evidence

Local evidence included the package inventory, subject list/source/table, NKI-TRT README and phenotype table, wider NKI MRI-QC table, label notice/definitions, processing scripts, accepted cohort manifests/QC hashes, and raw archive members. Authoritative corroboration used the official NKI test-retest page (`https://fcon_1000.projects.nitrc.org/indi/pro/eNKI_RS_TRT/FrontPage.html`) and primary NKI paper (`https://doi.org/10.3389/fnins.2012.00152`).

## Results

- Archive hash matched inventory: `9c6899707d51a009ea7fc670090cc060a2dc60e8426216ff6129f88814642570`.
- 201 safe members exactly match disk; 180 files, 160 NIfTIs, 20 subjects.
- Candidates/QC: 20 native and 20 MNI152; 40 verified, 0 failed, 0 blocked, 0 unknown observed IDs.
- Lineage: 20 confirmed participant groups and 20 test-retest groups. All selected session IDs, counterpart sessions, and temporal roles remain unresolved.
- Cross-cohort overlap: TRT-5/RS-3 share source ID 1427581; TRT-14/RS-14 share 3808535. Fifteen TRT IDs occur in supplied wider NKI metadata; no exact canonical file/voxel duplicates were found.
- Label notice: 397 ID records across eight subjects; 12 annotation-only temporal-pole records, 385 not applicable to canonical DKT31, 0 exclusions.

## Validation

- Automated tests passed 8/8 twice.
- QC and metadata generation ran twice with identical results and byte-identical six-artifact hashes.
- Existing QC implementation/tolerances and dictionary were unchanged.
- Accepted Extra-18, MMRR-21, and NKI-RS-22 artifact and archive hashes remained unchanged.
- Raw NKI-TRT archive hash remained equal to inventory; no raw file was renamed or modified.

## Outcome

NKI-TRT-20 passes this scoped checkpoint. Participant-grouped splitting is technically supportable only with cross-cohort participant IDs enforced, but no split was created. The NKI-RS-22-16 session conflict, NKI-TRT session roles, licensing, and Dataverse v2/OSF v3 equivalence remain unresolved.
