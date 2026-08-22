# Phase 1A Raw Organization and File Inventory Log

## Initiation

- Date: 2026-08-23
- Phase: 1A — Dataset foundation
- Milestone scope: verify downloaded raw-file organization and create a file-level integrity inventory; do not begin scan inventory or quality control.
- Skill: `brain-segmentation-research` (repository-local; no explicit version declared)
- Intended deliverable: one inventory row per downloaded file with relative path, filename, size, and SHA-256; an evidence-based organization report; updated project state.

## Initiating prompt

> Use `$brain-segmentation-research`.
>
> Verify the Mindboggle-101 organization under `data/raw/mindboggle101`.
> Create an inventory containing relative path, filename, size and SHA-256 checksum for every downloaded file.
>
> Do not extract archives, modify raw files, or begin quality control yet.
> Report missing, unexpected or incorrectly placed files and update the research log and `PROJECT_STATE.md`.

## Observed inputs

- Raw root existed with 24 files in five populated category trees plus an empty `extracted/` directory.
- Total observed size: 7,984,131,445 bytes.
- Harvard Dataverse API for DOI `10.7910/DVN/HMQKCK` reported version 2 with 24 files.
- The project data page's broader v3 (2019-04-03) designation does not match the Dataverse version number; equivalence remains unverified.

## Validation result

### Passed

- Created `metadata/raw_file_inventory.csv` with the exact columns `relative_path`, `filename`, `size_bytes`, and `sha256`.
- Inventory contains 24 unique relative paths and covers all 24 observed raw files.
- Inventory byte total equals the raw tree byte total: 7,984,131,445.
- All recorded filenames and sizes match the corresponding local files.
- All SHA-256 values have valid format and reproduced on a second complete hashing pass.
- Harvard Dataverse v2 comparison found 0 missing, 0 unexpected, 0 duplicate-name, and 0 size-mismatched files.
- `extracted/` contains 0 files.
- Git boundary check found 0 tracked raw files and 0 raw files escaping `.gitignore`.

### Failed

- None.

### Skipped

- Archive opening/listing and integrity testing, extraction, scan-level inventory, MRI/label pairing, and quality control were not performed by instruction.

### Blocked or unverified

- Exact equivalence to the OSF primary-repository v3 organization is unverified.
- Exact source-directory fidelity is unverified because the Dataverse record has no directory labels and the OSF hierarchy was unavailable for comparison.
- Standalone bundled license/changelog evidence is unavailable in both the local and Dataverse v2 24-file sets; licensing reconciliation remains blocked for human review.
- Retrieval date and download mechanism were not derivable from the files and were not inferred.
- Raw-data-dependent scientific checks remain unverified because archives were not extracted or inspected.

## Raw-data preservation

No raw file was written, moved, renamed, deleted, or extracted during this task. Only read operations and hashing were performed under `data/raw/mindboggle101/`; generated artifacts were written under `metadata/`, `docs/`, and `research_log/`.
