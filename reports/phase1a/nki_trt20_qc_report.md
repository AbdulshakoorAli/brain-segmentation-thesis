# NKI-TRT-20 Phase 1A Archive, QC, Lineage, and Overlap Report

## Checkpoint decision

NKI-TRT-20 passes this scoped Phase 1A checkpoint. All 40 canonical candidates are verified: 20 native and 20 MNI152 skull-stripped T1/manual-DKT31 pairs. All 20 participant groups and study-design repeat groups are resolved, but the included acquisition/session, counterpart session, and scan/rescan role remain unresolved for every participant.

Two participant groups overlap NKI-RS-22 and must remain grouped across cohorts. No split was created. OASIS-TRT-20 and every other unrequested cohort were not processed.

## Archive and inventory

- Archive SHA-256 matched inventory and remained unchanged: `9c6899707d51a009ea7fc670090cc060a2dc60e8426216ff6129f88814642570`.
- Gzip/tar parsing passed.
- Members: 201 (180 regular files and 21 directories).
- Absolute paths, traversal paths, duplicate paths, links, special entries, and overwrite risks: 0.
- Archive and extracted disk paths match exactly: 201/201.
- Extracted NIfTIs: 160 across 20 subjects.
- Full-head T1: 40; skull-stripped T1: 40; manual DKT31: 40; auxiliary manual+aseg: 40.
- Native NIfTIs: 80; MNI152 NIfTIs: 80.
- Unexpected NIfTIs: 0.
- Canonical candidates: 20 native and 20 MNI152; missing or ambiguous pairs: 0.

## Technical QC

The existing reusable implementation in `src/brain_segmentation/qc.py` was used unchanged with the accepted 62-row dictionary and affine tolerances (`rtol=1e-5`, `atol=1e-5`).

- Verified: 40/40; failed: 0; blocked: 0.
- Native: 20/20 verified; MNI152: 20/20 verified.
- Every pair passed parsing, shape, affine, orientation, spacing, declared-space, finite-value, MRI content/variation, integer-label, segmentation nonempty, label-vocabulary, technical overlap, and exact-duplicate checks.
- Native geometry: all `192x256x256`, `LAS`; spacing values are approximately 1 mm and match within each pair.
- MNI152 geometry: all `182x218x182`, `LAS`, `1;1;1`.
- Unknown observed label IDs: none.
- Exact within-cohort or accepted-cross-cohort compressed/voxel duplicates: none.

Automated tests passed twice (8/8 each). Two QC and metadata runs produced byte-identical outputs:

- manifest: `d24391c8293b0694e8b2552ec23764e4164faa44ecc33c62f06af5ef2b66cbae`
- pair QC: `9f4b9d302804ab7cc4b5aa0a4e329157ba5a70ff6e34933d0b731b64aa9c05d3`
- failures: `12b81b051d62fd473e837ac095ce95d2bd03816221897b3b674884b3790ce753`
- lineage: `6832bc3d7c558acca7dc068cd4010c63914a1e0ab61002ddf8232713e7e20441`
- label issues: `c1e1cb8de1e97c7b2f5cc7a0f43b773bc581228b698372b5363fab3793d1493b`
- overlap review: `26a903fce5650b93d69a439e65c892cb3ee0e6a5a6fc159894afe672098fb3d6`

No shared QC implementation changed, so previous cohort voxel QC was not rerun. Exact hashes confirm accepted Extra-18, MMRR-21, and NKI-RS-22 artifacts remained unchanged.

## Lineage and repeat acquisitions

The subject list, source table, and NKI-TRT phenotype table consistently identify 20 unique source participants. The local README describes 20 selected participants from a 24-subject NKI test-retest dataset. The official NKI documentation calls it a multiband test-retest pilot primarily composed of participants from the initial NKI-RS, and the primary NKI paper describes the 24-participant pilot release.

- Confirmed participant groups: 20.
- Confirmed study-design repeat-acquisition groups: 20.
- Included canonical acquisitions: one per participant, represented in native and MNI152 space.
- Exact included session identifiers: 0 resolved, 20 unresolved.
- Scan/rescan roles: 0 resolved, 20 unresolved.
- Counterpart session identifiers: 0 resolved, 20 unresolved.

No acquisition identifier or temporal role was inferred from filenames or numbering.

## Cross-cohort NKI overlap

Exact supplied source IDs confirm:

- `NKI-TRT-20-5` and `NKI-RS-22-3` are participant `1427581`.
- `NKI-TRT-20-14` and `NKI-RS-22-14` are participant `3808535`.

These pairs use identical `participant_group_id` values. Their canonical products are not exact file or decoded-voxel duplicates, but absence of an exact duplicate does not resolve whether their underlying acquisitions differ.

Fifteen TRT source IDs occur in the supplied wider `NKI.1-39.NumbersQC.csv` table. Five do not: subjects 1-4 and 11. The wider table provides an external NKI session string for those 15 matches, but no local evidence proves that it is the Mindboggle NKI-TRT canonical session, so it is retained only as external evidence.

No exact participant-source match was found with another Mindboggle cohort beyond the two NKI-RS matches. The official statement that the pilot was primarily composed of initial NKI-RS participants supports cohort-level relationship, not additional row-level identities.

The existing NKI-RS-22-16 conflict between `MR_3927656_3303` and `MR_3927656_3268` remains unresolved and was not altered.

## Label-issue review

The multiline March 2019 notice contains 397 subject/ID records across eight NKI-TRT subjects:

| Subject | Issue-ID records | Annotation only | Not applicable to canonical DKT31 |
|---|---:|---:|---:|
| NKI-TRT-20-5 | 66 | 2 | 64 |
| NKI-TRT-20-6 | 67 | 2 | 65 |
| NKI-TRT-20-9 | 18 | 0 | 18 |
| NKI-TRT-20-12 | 7 | 0 | 7 |
| NKI-TRT-20-13 | 57 | 2 | 55 |
| NKI-TRT-20-14 | 64 | 2 | 62 |
| NKI-TRT-20-16 | 60 | 2 | 58 |
| NKI-TRT-20-20 | 58 | 2 | 56 |

The 12 annotation-only records are metadata-mentioned temporal-pole IDs 1033/2033. The remaining 385 records are outside the accepted canonical DKT31 vocabulary and are classified not applicable to the canonical target. Anatomical names are populated only when documented in the supplied label definitions; missing names remain blank. Current canonical data contain none of the notice IDs.

Actions: 0 exclusions, 12 annotation-only, 385 not applicable, 0 unresolved classifications. The exact product referenced by the notice remains unresolved.

## Final accounting

### Passed

- Archive checksum, integrity, safety, extraction, and exact disk reconciliation.
- Complete inventory and 40 same-subject/same-space candidates.
- 40/40 unchanged technical QC results.
- 20 participant and repeat-acquisition groups supported by source/study evidence.
- Two deterministic test, QC, and metadata runs.
- Prior-cohort artifact and archive preservation.

### Failed

- None.

### Skipped

- Full-head T1 and manual+aseg as canonical targets.
- OASIS-TRT-20 and all other cohorts.
- Splits, loader, training, and visualization.

### Unverified

- All 20 included/counterpart session identifiers and scan/rescan roles.
- Acquisition relationship between the two shared NKI-RS/NKI-TRT participants.
- Additional row-level identities implied only by the statement that the pilot was primarily drawn from initial NKI-RS.
- Exact label-notice product, external NKI coverage beyond supplied metadata, scientific/clinical validity, and source-directory fidelity.
- NKI-RS-22-16 session conflict, licensing, and Dataverse v2/OSF v3 equivalence.

### Blocked

- Licensing reconciliation requires human review.
- Phase-wide splitting awaits remaining-cohort lineage and a final global overlap audit.

## Splitting readiness and next task

NKI-TRT-20 is safe for participant-grouped splitting only if `participant_group_id` is used, native/MNI152 products remain together, and the two shared NKI-RS participants are kept in the same split across cohorts. Any external NKI data must be matched by source ID before inclusion.

Exact next recommended task: human-review the unresolved NKI-TRT session/counterpart mapping and the two cross-cohort participant groups, then explicitly authorize one next Phase 1A cohort. Do not create phase-wide splits until the intended cohorts and global overlap audit are complete.
