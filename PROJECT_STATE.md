# Brain Segmentation Research State

## Project
- Objective: Build a reproducible foundation for brain MRI segmentation research using Mindboggle-101 T1 MRI and manual DKT cortical labels.
- Dataset and version: Mindboggle-101 individual brains; upstream reports v3 (2019-04-03), local package version unverified because no data are present.
- Current phase: Phase 1A — Dataset foundation
- Current milestone: Milestone 1 — Dataset source and project initialization (complete)
- Last updated: 2026-08-22

## Completed
- Repository instructions created — `AGENTS.md`.
- Source, scope, upstream version status, and licensing questions recorded — `docs/dataset_source_and_license.md`.
- No-download acquisition procedure recorded — `docs/acquisition_plan.md`.
- Header-only proposed schemas created — `metadata/scan_manifest.csv`, `metadata/manifest_data_dictionary.csv`, and `metadata/dkt_label_dictionary.csv`.
- Initiating prompt recorded — `research_log/phase-1a-initiation.md`.
- Raw neuroimaging files, downloaded packages, derived caches, and Python caches excluded — `.gitignore`.

## In progress
- None. Work is stopped at the requested Milestone 1 boundary.

## Blocked
- Dataset acquisition — requires human licensing review and explicit later authorization; downloading was prohibited for this milestone.
- Package/component license reconciliation — requires the exact repository package and bundled notices.
- Scan inventory, MRI/label pairing, participant/acquisition lineage, and all image/label quality checks — require raw data.
- DKT label rows — require the authoritative label-definition material from the acquired package or another verified authoritative source.
- Leakage-safe train/validation/test assignments — require verified grouping lineage and are outside this milestone.
- Loader contract and implementation — require inspection of the actual package structure and are outside this milestone.

## Decisions
- 2026-08-22 — Use `data/raw/mindboggle-101/` as the planned immutable raw-data location — separates original source artifacts from metadata and derived outputs.
- 2026-08-22 — Record v3 (2019-04-03) only as upstream-reported — no local package exists to verify version metadata.
- 2026-08-22 — Leave all proposed CSV schemas header-only — avoids inventing participants, files, label IDs, or validation outcomes.
- 2026-08-22 — Treat licensing as unresolved — available repository-level and component-level descriptions must be reconciled by a human reviewer.

## Validation
- Proposed CSV schema structure — passed — exact expected headers, unique columns, and successful header parsing: scan manifest 25 columns, manifest dictionary 7 columns, DKT dictionary 5 columns; see `research_log/phase-1a-initiation.md`.
- CSV data rows are absent — passed — each proposed schema has 0 data rows.
- Phase 1A directory structure — passed — `data/raw/`, `data/derived/`, `data/cache/`, `docs/`, `metadata/`, and `research_log/` exist.
- Milestone boundary — passed — 0 raw files, 0 split-assignment files, 0 source implementation files, and 0 test implementation files were found.
- Ignore protections — passed — required raw neuroimaging, raw storage, derived/cache, and Python-cache patterns are present in `.gitignore`.
- MRI/label file parsing, pairing, shapes, affines, orientations, spacings, finite values, intensity variation, label vocabulary, overlap, duplicates, and lineage — blocked — raw data intentionally unavailable.
- Dataset/package version and bundled license notices — unverified — raw package intentionally unavailable.

## Next milestone
- After human licensing approval and separate authorization to download, acquire and integrity-check the exact individual-brains package, record its version/checksums/notices, then begin Milestone 2 inventory. Acceptance criteria: acquisition provenance and licenses are documented from observed artifacts, raw files remain immutable, and manifest rows are derived only from inspected source data.
