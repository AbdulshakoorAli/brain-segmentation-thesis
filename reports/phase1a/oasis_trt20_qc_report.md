# OASIS-TRT-20 Phase 1A Archive, QC, Lineage, and Overlap Report

## Checkpoint decision

OASIS-TRT-20 passes this scoped Phase 1A checkpoint. All 40 canonical candidates are verified: 20 native and 20 MNI152 skull-stripped T1/manual-DKT31 pairs. Participant, acquisition, test/retest role, repeat group, and external counterpart session are resolved for all 20 included acquisitions.

The archive contains one included session from each of 20 distinct OASIS-1 reliability participants: 18 tests (MR1) and two retests (MR2). Native and MNI152 files are two representations of the included acquisition, not repeat acquisitions. No combined manifest or split was created.

## Archive and inventory

- Archive SHA-256 matched inventory and remained unchanged: `9c26c7846293a74c94270d9b1c977bd180e084690a82538f4848d960be41137b`.
- Gzip/tar parsing passed.
- Members: 201 (180 regular files and 21 directories).
- Absolute paths, traversal, duplicate member paths, links, special entries, and overwrite risks: 0.
- Extracted paths match archive members exactly: 201/201.
- Extracted files: 180, including 160 NIfTIs across 20 subjects.
- Full-head T1: 40; skull-stripped T1: 40; manual DKT31: 40; auxiliary manual+aseg: 40.
- Native NIfTIs: 80; MNI152 NIfTIs: 80; unexpected NIfTIs: 0.
- Canonical candidates: 20 native and 20 MNI152; missing or ambiguous pairs: 0.

## Technical QC

The existing reusable implementation in `src/brain_segmentation/qc.py` was used unchanged with the accepted 62-row DKT dictionary and affine tolerances (`rtol=1e-5`, `atol=1e-5`).

- Verified: 40/40; failed: 0; blocked: 0.
- Native: 20/20 at `256x256x160`, `ASL`, `1;1;1`.
- MNI152: 20/20 at `182x218x182`, `LAS`, `1;1;1`.
- Every pair passed parsing, shape, affine, orientation, spacing, declared-space, finite-value, MRI content/variation, integer-label, segmentation nonempty, vocabulary, technical overlap, and exact-duplicate checks.
- Unknown observed label IDs: none.
- Exact compressed-file, decoded MRI, decoded label, or whole-pair duplicates within OASIS-TRT-20: none.
- Exact file or decoded-voxel duplicates against accepted Extra-18, MMRR-21, NKI-RS-22, and NKI-TRT-20 canonical data: none.

Automated tests passed 8/8 twice. Two QC and metadata runs produced byte-identical outputs:

- manifest: `8baede86d0b275544400aef523414c4b6b43908a0b6b31d9567595e7e64e3518`
- pair QC: `f71eb4a99646b1d45715cb0ac936571d0d58cbdda6833fdb3e8bf5aa3c6e1f87`
- failures: `12b81b051d62fd473e837ac095ce95d2bd03816221897b3b674884b3790ce753`
- lineage: `44e706d79710aae1346a7bd4c30c7f2565631459fc872f6a9f55ed2db3e52889`
- label issues: `d6fcc242332b793a5802ee0f1483517ca1caaca753fa1761d9f6e35ab007e966`
- overlap review: `8537db3db6ee8d982b56a006629c296b9a3e7d1f2a651b37f9f6062a14425e8b`

No shared QC implementation changed. Accepted prior-cohort artifacts and all five reviewed archive hashes remained unchanged. The accepted shared NKI groups for source participants 1427581 and 3808535 were explicitly revalidated.

## Participant and acquisition lineage

The subject-source table identifies each included session. The supplied OASIS reliability README independently lists 40 sessions: MR1 as `TEST`, MR2 as `RETEST`, with a shared `OAS1_<number>` participant identifier. Every included source session has an explicit counterpart.

- Confirmed participant groups: 20; unresolved: 0.
- Confirmed repeat-acquisition groups: 20.
- Included sessions: 18 MR1 tests and 2 MR2 retests.
- Counterpart session identifiers: 20/20 resolved.
- Canonical repeat pairs within this archive: 0, because only one session per participant is included.

No lineage was inferred from the Mindboggle subject number or filename alone.

## OASIS overlap review

All 20 participants are confirmed members of the external OASIS-1 cross-sectional reliability release. Official OASIS documentation describes 416 OASIS-1 participants and a 20-participant reliability subset scanned again within 90 days; the primary OASIS-1 paper reports the same design.

- Wider OASIS-1 participant overlap: 20/20 confirmed.
- External counterpart-session overlap: 20/20 confirmed through MR1/MR2 rows.
- Participant overlap with another Mindboggle cohort: 0.
- Exact acquisition/file/voxel overlap with another accepted Mindboggle cohort: 0.
- Relationship to OASIS-2, OASIS-3, or other external OASIS derivatives: unresolved because no supplied row-level mapping supports it.

## Label-issue review

The March 2019 notice contains nine issue-ID records across eight subjects:

- `OASIS-TRT-20-2`: 1033.
- `OASIS-TRT-20-3`: 2033.
- `OASIS-TRT-20-4`: 1033.
- `OASIS-TRT-20-6`: 2033.
- `OASIS-TRT-20-10`: 1032.
- `OASIS-TRT-20-12`: 2032 and 2033.
- `OASIS-TRT-20-14`: 2033.
- `OASIS-TRT-20-20`: 2032.

These are documented eliminated frontal/temporal pole IDs and are absent from current canonical voxels. Actions: 9 annotation-only, 0 exclusions, 0 not-applicable, and 0 unresolved classifications. The exact distributed product referenced by the notice remains unresolved.

## Final accounting

### Passed

- Archive checksum, integrity, safety, extraction fidelity, and raw preservation.
- Complete 20-subject inventory and 40 unambiguous canonical candidates.
- 40/40 technical QC results using unchanged rules.
- All participant, session, role, counterpart, and repeat groups resolved.
- Deterministic automated tests, QC, and metadata generation.
- Prior-cohort and accepted NKI-group preservation.

### Failed

- None.

### Skipped

- Full-head T1 and manual+aseg as canonical targets.
- Every other dataset, combined manifest, splits, loader, training, and visualization.

### Unverified

- Row-level overlap with OASIS-2, OASIS-3, or other OASIS derivatives.
- Exact label-notice product scope, source-directory fidelity, and scientific/clinical validity.
- Previously recorded NKI session/acquisition uncertainties, licensing, and Dataverse v2/OSF v3 equivalence.

### Blocked

- Licensing reconciliation requires human review.
- Combined-manifest and split work require explicit phase-transition approval and final global overlap review.

## Splitting readiness and next task

OASIS-TRT-20 is safe for participant-grouped splitting using `participant_group_id`, provided native/MNI152 products remain together and any external MR1/MR2 counterpart is assigned to the same group. No split was created.

Exact next recommended task: human-review the completed five-cohort QC/lineage evidence and unresolved NKI/OASIS external relationships, then explicitly authorize creation of the combined 101-subject manifest and final global overlap audit; do not create splits until that audit passes.
