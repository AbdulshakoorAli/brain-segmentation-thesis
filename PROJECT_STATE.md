# Brain Segmentation Research State

## Project
- Objective: Build a reproducible foundation for brain MRI segmentation research using Mindboggle-101 T1 MRI and manual DKT cortical labels.
- Dataset and version: Mindboggle-101 individual brains; 24 local files match the Harvard Dataverse v2 filename/size listing, while the project page reports OSF/project v3 (2019-04-03); equivalence is unverified.
- Current phase: Phase 1A — Dataset foundation
- Current milestone: Raw organization and file-level inventory (complete); scan-level Milestone 2 not started
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

## In progress
- None. Work is stopped at the requested raw-organization/file-inventory boundary; scan-level inventory and quality control have not started.

## Blocked
- Package/version provenance — the local set matches Harvard Dataverse v2 by filename and size, but its relationship to the OSF/project-level v3 designation is unverified.
- Package/component license reconciliation — no standalone license notice is present in the local or Dataverse v2 24-file listing; repository metadata and component terms require human review.
- Source-directory fidelity — Dataverse supplies no directory labels and the OSF hierarchy was unavailable, so the local category-folder layout cannot be proven identical to the acquisition source.
- Scan inventory, MRI/label pairing, participant/acquisition lineage, and all image/label quality checks — archives remain unextracted and these checks were deliberately not started.
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

## Validation
- Proposed CSV schema structure — passed — exact expected headers, unique columns, and successful header parsing: scan manifest 25 columns, manifest dictionary 7 columns, DKT dictionary 5 columns; see `research_log/phase-1a-initiation.md`.
- CSV data rows are absent — passed — each proposed schema has 0 data rows.
- Phase 1A directory structure — passed — `data/raw/`, `data/derived/`, `data/cache/`, `docs/`, `metadata/`, and `research_log/` exist.
- Initialization boundary (2026-08-22) — passed at that time — 0 raw files, 0 split-assignment files, 0 source implementation files, and 0 test implementation files were found.
- Ignore protections — passed — required raw neuroimaging, raw storage, derived/cache, and Python-cache patterns are present in `.gitignore`.
- MRI/label file parsing, pairing, shapes, affines, orientations, spacings, finite values, intensity variation, label vocabulary, overlap, duplicates, and lineage — skipped — archives remain unextracted and quality control was explicitly prohibited.
- Raw inventory coverage — passed — 24 unique rows cover 24 files totaling 7,984,131,445 bytes; filenames, relative paths, and sizes match observed files.
- SHA-256 reproducibility — passed — all 24 hashes reproduced on a second complete hashing pass.
- Harvard Dataverse v2 file-set comparison — passed — 0 missing, 0 unexpected, 0 duplicate-name, and 0 size-mismatched files.
- Extraction boundary — passed — `extracted/` contains 0 files; no archives were extracted or opened.
- Raw Git boundary — passed — 0 raw files are tracked and all 24 are covered by `.gitignore`.
- Raw organization — partially verified — semantic category placement is consistent, but exact source-directory fidelity is unverified.
- MRI/label quality control — skipped — explicitly outside this task and archives remain unextracted.
- Dataset/package version and bundled license notices — unverified — Dataverse-v2/OSF-v3 equivalence and component licensing remain unresolved.

## Next milestone
- Resolve licensing and Dataverse-v2/OSF-v3 provenance with human review, then separately authorize a non-destructive archive inspection/extraction plan before beginning scan-level Milestone 2. Acceptance criteria: applicable terms and source version are recorded, the file-level inventory remains reproducible, extraction destinations preserve the raw archives, and no scan manifest rows are created before actual contents are inspected.
