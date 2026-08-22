# Brain Segmentation Research State

## Project
- Objective: Build a reproducible foundation for brain MRI segmentation research using Mindboggle-101 T1 MRI and manual DKT cortical labels.
- Dataset and version: Mindboggle-101 individual brains; 24 local files match the Harvard Dataverse v2 filename/size listing, while the project page reports OSF/project v3 (2019-04-03); equivalence is unverified.
- Current phase: Phase 1A — Dataset foundation
- Current milestone: Raw organization and file-level inventory complete; Extra-18 archive extraction and candidate scan inventory complete; NIfTI header/voxel quality control not started
- Last updated: 2026-08-23

## Completed
- Repository instructions created — `AGENTS.md`.
- Source, scope, upstream version status, and licensing questions recorded — `docs/dataset_source_and_license.md`.
- No-download acquisition procedure recorded — `docs/acquisition_plan.md`.
- Header-only proposed schemas created — `metadata/scan_manifest.csv`, `metadata/manifest_data_dictionary.csv`, and `metadata/dkt_label_dictionary.csv`.
- Initiating prompt recorded — `research_log/phase-1a-initiation.md`.
- Raw neuroimaging files, downloaded packages, derived caches, and Python caches excluded — `.gitignore`.
- Raw-file inventory created — `metadata/raw_file_inventory.csv` contains relative path, filename, byte size, and SHA-256 for all 24 downloaded files.
- Raw organization assessed — `docs/raw_dataset_organization_report.md`; no missing or unexpected files against Harvard Dataverse v2.
- Prompt and validation evidence recorded — `research_log/phase-1a-raw-inventory.md`.
- Extra-18 archive checksum, gzip/tar integrity, member-path safety, and extraction validated — source archive unchanged; 183 safe members extracted to the requested previously absent target.
- Exact Extra-18 extracted structure recorded — `data/derived/manifests/extra18_extracted_structure.txt` contains 19 directories and 164 files.
- Extra-18 candidate scan manifest created — `data/derived/manifests/extra18_scan_inventory.csv` contains 18 native and 18 MNI152 same-subject/same-space candidate pairs.
- Extra-18 prompt, classification, metadata comparison, pairing, and validation evidence recorded — `research_log/phase-1a-extra18.md`.
- Reproducible Extra-18 inventory generator created — `scripts/inventory_extra18.ps1`.

## In progress
- None. Work is stopped at the requested Extra-18 archive-processing boundary; its NIfTI header/voxel quality control and every other cohort remain unprocessed.

## Blocked
- Package/version provenance — the local set matches Harvard Dataverse v2 by filename and size, but its relationship to the OSF/project-level v3 designation is unverified.
- Package/component license reconciliation — no standalone license notice is present in the local or Dataverse v2 24-file listing; repository metadata and component terms require human review.
- Source-directory fidelity — Dataverse supplies no directory labels and the OSF hierarchy was unavailable, so the local category-folder layout cannot be proven identical to the acquisition source.
- Remaining scan inventory and MRI/label pairing — only Extra-18 has been extracted and structurally paired; no other cohort was processed.
- Extra-18 usable-pair acceptance — 36 same-subject/same-space candidates exist, but NIfTI parsing, header compatibility, voxel checks, and duplicate/repeat evidence remain unverified.
- Participant/acquisition lineage — Extra-18 IDs were compared with supplied subject/source metadata, but lineage beyond its documented source field remains unverified.
- DKT label rows — local `label_definitions.txt` is inventoried but has not yet been scientifically reviewed or used to derive dictionary rows.
- Leakage-safe train/validation/test assignments — require verified grouping lineage and are outside this milestone.
- Loader contract and implementation — require inspection of the actual package structure and are outside this milestone.

## Decisions
- 2026-08-22 — Initially plan `data/raw/mindboggle-101/` as immutable raw storage — superseded on 2026-08-23 by the observed user-specified `data/raw/mindboggle101/` path.
- 2026-08-22 — Record v3 (2019-04-03) as project-page-reported — retained as a distinct upstream designation after the Dataverse v2 set was observed.
- 2026-08-22 — Leave all proposed CSV schemas header-only — avoids inventing participants, files, label IDs, or validation outcomes.
- 2026-08-22 — Treat licensing as unresolved — available repository-level and component-level descriptions must be reconciled by a human reviewer.
- 2026-08-23 — Use `data/raw/mindboggle101/` as the observed immutable raw root — this is the user-specified populated path; do not rename or move raw files.
- 2026-08-23 — Treat Harvard Dataverse v2 and OSF/project v3 as distinct unresolved version designations — matching filenames/sizes do not prove repository-version equivalence.
- 2026-08-23 — Inventory all files, including currently out-of-scope components — the requested artifact must cover every downloaded file without deleting or filtering raw data.
- 2026-08-23 — Extract only `Extra-18_volumes.tar.gz` after checksum, gzip/tar, path-traversal, and entry-type checks passed — preserve its distributed `Extra-18_volumes/` top-level directory beneath the requested target.
- 2026-08-23 — Use skull-stripped `t1weighted_brain` plus `labels.DKT31.manual` as the canonical candidate pair — retain full-head T1 and `manual+aseg` as explicitly inventoried same-space alternatives.
- 2026-08-23 — Mark Extra-18 rows `matched_pending_nifti_qc` — filename, subject, and space matching does not substitute for NIfTI header and voxel validation.

## Validation
- Proposed CSV schema structure — passed — exact expected headers, unique columns, and successful header parsing: scan manifest 25 columns, manifest dictionary 7 columns, DKT dictionary 5 columns; see `research_log/phase-1a-initiation.md`.
- CSV data rows are absent — passed — each proposed schema has 0 data rows.
- Phase 1A directory structure — passed — `data/raw/`, `data/derived/`, `data/cache/`, `docs/`, `metadata/`, and `research_log/` exist.
- Initialization boundary (2026-08-22) — passed at that time — 0 raw files, 0 split-assignment files, 0 source implementation files, and 0 test implementation files were found.
- Ignore protections — passed — required raw neuroimaging, raw storage, derived/cache, and Python-cache patterns are present in `.gitignore`.
- MRI/label file parsing, shapes, affines, orientations, spacings, finite values, intensity variation, label vocabulary, overlap, and duplicate-content checks — skipped — explicitly outside the Extra-18 archive-processing task.
- Raw inventory coverage — passed — 24 unique rows cover 24 files totaling 7,984,131,445 bytes; filenames, relative paths, and sizes match observed files.
- SHA-256 reproducibility — passed — all 24 hashes reproduced on a second complete hashing pass.
- Harvard Dataverse v2 file-set comparison — passed — 0 missing, 0 unexpected, 0 duplicate-name, and 0 size-mismatched files.
- Prior extraction boundary (2026-08-23 raw-inventory task) — passed at that time — `extracted/` contained 0 files and no archives had been opened.
- Raw Git boundary — passed — 0 raw files are tracked and all 24 are covered by `.gitignore`.
- Raw organization — partially verified — semantic category placement is consistent, but exact source-directory fidelity is unverified.
- Extra-18 archive checksum — passed — recomputed SHA-256 exactly matches `metadata/raw_file_inventory.csv`.
- Extra-18 archive integrity and safety — passed — gzip EOF validation and tar listing passed; 183 members, 0 unsafe paths, and 0 link/special entries.
- Extra-18 extraction fidelity — passed — 183 archive member paths exactly match 183 extracted entries; 0 missing and 0 unexpected disk paths.
- Extra-18 extracted inventory — passed — 164 files, 144 NIfTIs, 18 subjects, 72 native NIfTIs, and 72 MNI152 NIfTIs.
- Extra-18 metadata comparison — passed — all 18 extracted IDs occur in both the supplied subject list and subject-source table.
- Extra-18 candidate pairing — passed at structural matching scope — 18 native and 18 MNI152 candidates; 0 missing/ambiguous canonical pairs and 0 cross-space path mismatches.
- Extra-18 unexpected files — observed — `.DS_Store` and `._.DS_Store` are non-NIfTI archive-root metadata artifacts; no unexpected subject NIfTIs were found.
- Extra-18 MRI/label quality control — skipped — all 36 candidate rows remain pending NIfTI header and voxel-level validation.
- Dataset/package version and bundled license notices — unverified — Dataverse-v2/OSF-v3 equivalence and component licensing remain unresolved.

## Next milestone
- Process only the 36 canonical Extra-18 candidates in `data/derived/manifests/extra18_scan_inventory.csv` through NIfTI header and voxel-level quality control. Record parsing, image/label shape, affine compatibility, orientation, spacing, finite values, MRI content and intensity variation, label integrality and IDs, segmentation nonemptiness, spatial overlap, and duplicate/repeat evidence without modifying or resampling raw files. Keep licensing reconciliation and Harvard Dataverse v2 versus OSF/project v3 equivalence unresolved for human review; do not process another cohort yet.
