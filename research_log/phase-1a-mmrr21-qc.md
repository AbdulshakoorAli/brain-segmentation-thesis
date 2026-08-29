# Phase 1A MMRR-21 Archive and NIfTI QC Research Log

## Initiation

- Date: 2026-08-26.
- Skill: `brain-segmentation-research` (repository-local; no explicit version declared).
- Phase: 1A — Dataset foundation.
- Scope: only `MMRR-21_volumes.tar.gz`; archive validation/extraction, inventory, lineage evidence, canonical pairing, and unchanged reusable QC.
- Intended outputs: MMRR-21 manifest, pair QC, failures, report, research log, and updated project state.
- Explicit exclusions: other cohorts, splits, loader, training, and visualization.

## Initiating prompt

The user accepted the Extra-18 pilot and requested processing of only the MMRR-21 volume archive. Required work included archive checksum/integrity/safety, extraction without overwrite, structure and file classification, comparison with three supplied metadata sources, faithful lineage recording, same-subject/same-space canonical pairing, unchanged reusable QC with the existing DKT dictionary, two test and QC runs, deterministic comparison, raw preservation, requested artifacts, and a scoped checkpoint decision.

## Archive and extraction evidence

- Archive size: 843,015,849 bytes.
- Inventory, pre-extraction, and post-QC SHA-256: `73b27f5ccce27a47e6cf03b9a1adc64b191d677009340feb531793e0fa83eeb1`.
- Gzip/tar listing: passed.
- Members: 211 unique; unsafe paths: 0; duplicate member paths: 0; links/special entries: 0.
- Destination absent before extraction; overwrite risk: 0.
- Archive/disk comparison: 211/211 exact; missing 0; unexpected 0.
- Extracted contents: 22 directories, 189 files, 168 NIfTIs, and 21 subjects.

## Inventory and metadata evidence

- NIfTIs: 84 native and 84 MNI152; 42 each of full-head T1, skull-stripped T1, manual DKT31, and auxiliary `manual+aseg`; unexpected NIfTIs: 0.
- Candidates: 21 native and 21 MNI152; missing/ambiguous: 0.
- All 21 subject identifiers matched subject-list, subject-source, and MMRR-21 scan-information rows.
- Source values, Visit IDs, and scan-information SubjectIDs copied verbatim; no demographic attributes copied to the manifest.
- Explicit supplied repeat-mapping strings exist for subjects 1–10 only. Subjects 11–21 are marked as having no supplied repeat row, not inferred to lack repeats.
- Five label-issue notices were recorded. Their IDs (`1032`, `1033`, `2032`, `2033`) were absent from canonical voxel data and were not added to the dictionary.

## Implementation boundary

- Accepted `src/brain_segmentation/qc.py` was not changed; before/after SHA-256: `763f6e90e9b7494560cf40a39378cbbfaa48477326c41a31b7e1a6647c9c7b4c`.
- Existing 62-row dictionary reused unchanged; SHA-256: `76a113acec22cad1ec1fcb67fedc7f2b3d6a8eafe6e53ca6c5873e8a64651306`.
- Added `scripts/inventory_mmrr21.py` and `scripts/run_mmrr21_qc.py` as cohort-scoped orchestration only.
- Accepted Extra-18 output hashes remained unchanged, so no Extra-18 regression rerun was required by the prompt's conditional rule.

## Validation runs

- Test run 1: 8/8 passed in 0.40 seconds.
- MMRR-21 QC run 1: 42 verified, 0 failed, 0 blocked; 0 failure rows; no unknown IDs.
- Test run 2: 8/8 passed in 1.51 seconds.
- MMRR-21 QC run 2: 42 verified, 0 failed, 0 blocked; 0 failure rows; no unknown IDs.
- Deterministic hashes matched between runs:
  - `mmrr21_pair_qc.csv`: `ee828bcc23214a02ba68e0054a20a18a2f51b39fd2a610a82d517531767e8568`.
  - `mmrr21_failures.csv`: `12b81b051d62fd473e837ac095ce95d2bd03816221897b3b674884b3790ce753`.
  - `mmrr21_scan_inventory.csv`: `1f6b77a6e88a33e5c7671bca96a2fb2c10ab569f544ddec11c7ea671a0224a12`.

## Passed

- Archive, extraction, inventory, metadata matching, pairing, all 42 technical QC results, tests, and deterministic reproduction.
- MMRR-21 passes this scoped Phase 1A checkpoint.

## Failed

- None.

## Skipped

- Auxiliary files as canonical targets, other cohorts, splits, loader, training, and visualization.

## Unverified

- Canonical scan/rescan identity; repeat mappings absent for subjects 11–21; relationship of label-issue notices to canonical files; version equivalence; scientific/clinical validity.

## Blocked

- Licensing reconciliation and leakage-safe splitting pending human review/lineage resolution.

## Exact next recommendation

Human-review the MMRR-21 label-issue notices and scan/rescan evidence, reconcile external participant/acquisition grouping for all 21 subjects, then explicitly authorize one next cohort inventory/QC milestone. Do not create splits yet.

