# NKI-RS-22 Phase 1A Archive, QC, Lineage, and Label-Issue Report

## Checkpoint decision

NKI-RS-22 passes this scoped Phase 1A checkpoint. All 44 canonical candidates are technically verified: 22 native and 22 MNI152 skull-stripped T1/manual-DKT31 pairs. Participant grouping is resolved for all 22 source participants. One acquisition identifier remains ambiguous, but it does not make participant grouping ambiguous.

No other cohort was processed. No split, loader, training code, visualization, resampling, normalization, reorientation, cropping, repair, or raw-file modification was performed. Licensing reconciliation and Harvard Dataverse v2 versus OSF/project v3 equivalence remain unresolved.

## Archive and extraction

- Archive: `data/raw/mindboggle101/archives/volumes/NKI-RS-22_volumes.tar.gz`.
- Inventory and post-processing SHA-256: `450588dcb8528b617c1472cb8119748f60481b6d40d2d10e6aafca21a8e078c4`.
- Gzip/tar parsing: passed.
- Members: 221 (198 regular files, 23 directories).
- Unsafe paths, duplicate member paths, links, and special entries: 0.
- Extraction target was absent before extraction, so overwrite risk was 0.
- Archive-to-disk correspondence: 221/221 exact paths; 0 missing and 0 unexpected.
- Extracted files: 198, including 176 NIfTIs.

## Inventory and pairing

- Subjects: 22 (`NKI-RS-22-1` through `NKI-RS-22-22`).
- Full-head T1: 44; skull-stripped T1: 44; manual DKT31: 44; auxiliary manual+aseg: 44.
- Native NIfTIs: 88; MNI152 NIfTIs: 88; ancillary MNI152 affine files: 22.
- Unexpected NIfTIs: 0.
- Native candidates: 22; MNI152 candidates: 22.
- Missing or ambiguous MRI/manual-DKT31 pairs: 0.

Every candidate uses matching subject and filename-declared coordinate space. Full-head T1 and manual+aseg products remain auxiliary.

## Technical NIfTI QC

The accepted implementation in `src/brain_segmentation/qc.py` was used unchanged with its existing affine tolerances (`rtol=1e-5`, `atol=1e-5`) and the existing 62-row DKT dictionary.

- Verified: 44/44; failed: 0; blocked: 0.
- Native verified: 22/22; MNI152 verified: 22/22.
- All pairs passed parsing, exact shape compatibility, affine, orientation, spacing, declared-space consistency, finite values, MRI content/variation, label integrality, segmentation nonemptiness, label vocabulary, technical brain overlap, and duplicate checks.
- MNI152 geometry: 22 pairs at `182x218x182`, `LAS`, `1;1;1`.
- Native geometry: 21 pairs at `192x256x256`, `LAS`, `1;1;1`; one pair at `256x256x256`, `LIA`, `1;1;1`. Each MRI matches its own label.
- Unknown observed label IDs: none.
- Exact compressed-file, decoded-voxel, label, or whole-pair duplicates: none.

Automated tests passed twice (8/8 each). Two QC and metadata runs produced byte-identical outputs:

- manifest: `320ce9fa34afc9629637b4c73f6888cb4a53ee48ffd03af7a9bcb334a02a24d3`
- pair QC: `b78256007d27df3eef197f2fea01967a9d80ce65fcc87a712c057761b029749f`
- failures: `12b81b051d62fd473e837ac095ce95d2bd03816221897b3b674884b3790ce753`
- lineage: `88f0201d4e4f136a2d2ae65adff115a8f933cbb164b996915250a415734ebdda`
- label issues: `808d770fbc0a33e452f97000da6c5173cb5f24e028e99344d0f8e90aeaebffcb`

The QC implementation, DKT dictionary, and accepted Extra-18/MMRR-21 artifacts retained their baseline hashes.

## Participant and acquisition lineage

All 22 Mindboggle IDs match the subject list and subject-source table. The source identifiers are 22 unique `NKI_Rockland_<number>` values, which support 22 distinct participant groups. Native and MNI152 rows for each subject are two products of one included acquisition.

The selected-22 phenotype table and MRI QC table agree on the session identifier for 21 participants. For `NKI-RS-22-16` (`NKI_Rockland_3927656`), they disagree: `MR_3927656_3303` versus `MR_3927656_3268`. The manifest leaves the acquisition identifier empty, records both candidates, and marks it ambiguous.

No supplied Mindboggle repeat table links these NKI subjects and no source participant ID repeats among the 22 included rows. This is evidence of no repeat relationship within the reviewed local selection, not proof that no acquisition exists outside it.

## Label-issue review

`label-issues_201903.txt` contains 18 subject/ID entries across seven NKI subjects:

| Subject | Metadata-mentioned IDs | Required action |
|---|---|---|
| NKI-RS-22-9 | 2033 | annotation only |
| NKI-RS-22-10 | 1033 | annotation only |
| NKI-RS-22-12 | 1033, 2033 | annotation only |
| NKI-RS-22-13 | 1033 | annotation only |
| NKI-RS-22-16 | 7, 8, 16, 24, 46, 47, 77, 80, 85, 1000, 2000 | not applicable to canonical DKT31; retain auxiliary provenance |
| NKI-RS-22-18 | 2033 | annotation only |
| NKI-RS-22-22 | 1033 | annotation only |

IDs 1033 and 2033 are documented eliminated temporal-pole IDs. IDs 7, 16, 24, 46, and 85 have documented noncortical names. No anatomical name was invented for 8, 47, 77, 80, 1000, or 2000 because the supplied label definitions do not document them in the reviewed blocks.

The notice states that errors were corrected in March 2019 but does not specify the distributed product. Current canonical labels contain none of these IDs, and the processing script constructs canonical DKT31 volumes using only the accepted cortical selection. Actions: 7 annotation-only entries, 11 not-applicable entries, 0 exclusions, and 0 unresolved action classifications. Product scope remains unresolved.

## Final accounting

### Passed

- Archive checksum, gzip/tar integrity, safety, extraction fidelity, and raw preservation.
- Complete 22-subject inventory and 44 unambiguous same-subject/same-space candidates.
- 44/44 technical QC results and two 8/8 automated-test runs.
- Deterministic QC and metadata artifacts across two runs.
- All 22 participant groups resolved from unique source identifiers.

### Failed

- None.

### Skipped

- Full-head T1 and manual+aseg as canonical targets.
- Every other cohort; splits, loader, training, and visualization.

### Unverified

- Exact acquisition/session identifier for `NKI-RS-22-16`.
- Temporal scan/rescan roles and acquisition relationships outside the supplied NKI selection.
- Exact product referenced by the March 2019 label notice.
- Cross-dataset NKI overlap, scientific/clinical validity, source-directory fidelity, licensing, and Dataverse v2/OSF v3 equivalence.

### Blocked

- Package/component licensing reconciliation requires human review.
- Phase-wide splitting remains blocked on completion of intended-cohort lineage and cross-dataset overlap review.

## Splitting readiness and next task

NKI-RS-22 is safe for participant-grouped splitting within this cohort using `participant_group_id`, provided native/MNI152 products remain together. The `NKI-RS-22-16` session ambiguity does not change its participant group. Combining with other NKI-derived datasets requires a separate source-ID overlap audit first.

Exact next recommended task: obtain human clarification for the `NKI_Rockland_3927656` session discrepancy and sign-off on the seven-subject label annotations, then explicitly authorize one next Phase 1A cohort; do not create phase-wide splits until intended-cohort lineage and cross-dataset overlap review are complete.
