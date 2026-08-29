# MMRR-21 Phase 1A Archive, Inventory, and NIfTI QC Report

## Scope and checkpoint decision

MMRR-21 passes this scoped Phase 1A archive, pairing, and technical NIfTI QC checkpoint. All 42 canonical candidates are verified: 21 native-space and 21 MNI152-space MRI/manual-DKT31 pairs. No candidate failed or was blocked.

Only `MMRR-21_volumes.tar.gz` was processed. Full-head T1 and `manual+aseg` files remain auxiliary. No other cohort, split, loader, training code, or visualization was processed. Phase 1A overall remains incomplete, and licensing reconciliation plus Harvard Dataverse v2 versus OSF/project v3 equivalence remain unresolved.

## Archive validation and extraction

- Inventory size: 843,015,849 bytes.
- Pre-extraction and post-QC SHA-256: `73b27f5ccce27a47e6cf03b9a1adc64b191d677009340feb531793e0fa83eeb1`; exact match to `metadata/raw_file_inventory.csv`.
- Full gzip/tar listing completed successfully.
- Archive members: 211 unique paths beneath the sole top-level directory `MMRR-21_volumes/`.
- Unsafe absolute, drive-qualified, UNC, or `..` traversal paths: 0.
- Duplicate archive member paths: 0.
- Links or special entries: 0; all entries were regular files or directories.
- Overwrite risk: none; `data/raw/mindboggle101/extracted/MMRR-21/` was absent before extraction.
- Extraction fidelity: 211 archive members exactly matched 211 disk entries; 0 missing and 0 unexpected.
- Extracted directories: 22. Extracted files: 189.

No source file was renamed, repaired, reoriented, normalized, cropped, resampled, or modified.

## File and candidate inventory

- Subjects: 21 (`MMRR-21-1` through `MMRR-21-21`).
- NIfTI files: 168 — 84 native and 84 MNI152.
- Full-head T1 volumes: 42.
- Skull-stripped T1 volumes: 42.
- Manual DKT31 volumes: 42.
- Auxiliary `manual+aseg` volumes: 42.
- Unexpected NIfTI files: 0.
- Ancillary MNI152 affine text files: 21.
- Native canonical candidates: 21.
- MNI152 canonical candidates: 21.
- Missing or ambiguous pairs: 0.

Canonical candidates use only exact same-subject/same-space `t1weighted_brain[.MNI152].nii.gz` and `labels.DKT31.manual[.MNI152].nii.gz` paths. The manifest records auxiliary paths separately.

## Metadata and lineage evidence

All 21 extracted subject IDs occur in the supplied subject list, subject-source table, and MMRR-21 scan-information README. The manifest records the supplied source value, scan-information Visit ID, and scan-information SubjectID verbatim. The 21 scan-information SubjectIDs are distinct.

The supplied repeat-scan section explicitly contains mapping text for only `MMRR-21-1` through `MMRR-21-10`; those strings are preserved verbatim in the manifest. It contains no row for `MMRR-21-11` through `MMRR-21-21`. Absence is recorded as unavailable evidence, not interpreted as absence of repeat acquisitions. The canonical NIfTI filenames themselves do not independently identify scan versus rescan. No split was created.

`label-issues_201903.txt` names `MMRR-21-1`, `MMRR-21-9`, `MMRR-21-17`, `MMRR-21-19`, and `MMRR-21-20` with IDs among `1032`, `1033`, `2032`, and `2033`. None of those IDs occurred in the inspected canonical manual-DKT31 NIfTIs. They were not added to the dictionary and did not create an observed voxel-QC failure. The relationship between that notice and these distributed canonical volumes remains a metadata/provenance follow-up.

## QC method and results

The accepted implementation in `src/brain_segmentation/qc.py` was used unchanged. Its SHA-256 remained `763f6e90e9b7494560cf40a39378cbbfaa48477326c41a31b7e1a6647c9c7b4c`. A cohort-scoped runner reused the existing 62-row DKT dictionary; no definitions were added.

All 42 pairs passed parsing, exact 3D shape compatibility, affine comparison (`rtol=1e-5`, `atol=1e-5`), orientation matching, spacing matching, file-declared space consistency, finite values, MRI nonemptiness and variation, label integrality, segmentation nonemptiness, label vocabulary, technical brain overlap, and exact duplicate analysis.

- Native shape/orientation/spacing: all 21 were `170x256x256`, `RPS`, and `1.20000005;1;1`.
- MNI152 shape/orientation/spacing: all 21 were `182x218x182`, `LAS`, and `1;1;1`.
- Maximum MRI/label affine elementwise absolute difference: `0`.
- Segmentation overlap fraction: `1.0` for every pair.
- Every label volume contained background `0` plus the same 62 defined DKT cortical IDs.
- Observed unknown label IDs: none.
- Exact compressed-file, decoded MRI, decoded label, or whole-pair voxel duplicates: none.

## Repeated validation and preservation

- Automated test run 1: 8/8 passed in 0.40 seconds.
- Automated test run 2: 8/8 passed in 1.51 seconds.
- MMRR-21 QC run 1: 42 verified, 0 failed, 0 blocked.
- MMRR-21 QC run 2: 42 verified, 0 failed, 0 blocked.
- Run-to-run artifact hashes matched exactly:
  - Pair QC: `ee828bcc23214a02ba68e0054a20a18a2f51b39fd2a610a82d517531767e8568`.
  - Failures: `12b81b051d62fd473e837ac095ce95d2bd03816221897b3b674884b3790ce753`.
  - Manifest: `1f6b77a6e88a33e5c7671bca96a2fb2c10ab569f544ddec11c7ea671a0224a12`.
- Existing DKT dictionary and all accepted Extra-18 CSV hashes remained unchanged.
- Identical QC artifacts across runs also reproduce all canonical source-file and decoded-voxel hashes.

## Final accounting

### Passed

- Archive checksum, integrity, safety, extraction, and disk correspondence.
- Subject/file classification and 42 same-subject/same-space canonical candidates.
- 42/42 technical pair QC results: 21 native and 21 MNI152.
- Metadata identifier matches and faithful recording of available lineage evidence.
- Two test runs, two QC runs, and byte-identical outputs.

### Failed

- None.

### Skipped

- Auxiliary full-head T1 and `manual+aseg` as canonical QC targets.
- All cohorts other than MMRR-21.
- Splits, loader, training, and visualization.

### Unverified

- Canonical scan-versus-rescan acquisition identity.
- Repeat-acquisition mapping for `MMRR-21-11` through `MMRR-21-21` because no supplied repeat-table rows exist for them.
- Relationship of the five label-issue notices to the canonical volumes, because the cited IDs were not observed.
- Dataverse v2 versus OSF/project v3 equivalence, source-directory fidelity, and scientific/clinical validity.

### Blocked

- Package/component licensing reconciliation requires human review.
- Leakage-safe splitting remains blocked until lineage evidence is reconciled across all relevant cohorts and external counterparts.

- Extracted file count: 189.
- NIfTI count: 168.
- Subject count: 21.
- Native candidate count: 21; native verified-pair count: 21.
- MNI152 candidate count: 21; MNI152 verified-pair count: 21.
- Missing or ambiguous pairs: none.
- Subjects requiring technical-QC investigation: none.
- Subjects requiring metadata/lineage investigation: `MMRR-21-1`, `MMRR-21-9`, and `MMRR-21-11` through `MMRR-21-21` (including `MMRR-21-17`, `MMRR-21-19`, and `MMRR-21-20`); see the two evidence categories above.
- Unknown label IDs observed in canonical volumes: none. Metadata-mentioned but unobserved IDs: `1032`, `1033`, `2032`, `2033`.
- Existing QC implementation worked unchanged: yes.
- Exact next recommended task: human-review the MMRR-21 label-issue notices and scan/rescan lineage evidence, reconcile external participant/acquisition grouping for all 21 subjects, then explicitly authorize the next single Phase 1A cohort inventory/QC milestone; do not create splits yet.

