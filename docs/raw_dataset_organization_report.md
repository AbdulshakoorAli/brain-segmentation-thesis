# Mindboggle-101 Raw Dataset Organization Report

## Scope

- Inspected root: `data/raw/mindboggle101/`
- Inspection date: 2026-08-23
- File inventory: `metadata/raw_file_inventory.csv`
- Inventory path basis: every `relative_path` is relative to `data/raw/mindboggle101/`
- Boundary: filenames, paths, byte sizes, and hashes only; archives were not opened or extracted, raw files were not modified, and MRI/label quality control was not started.

## Authoritative comparison

The local set was compared with the current Harvard Dataverse API record for DOI `10.7910/DVN/HMQKCK`. The API reported dataset version 2 and 24 files. Comparison used case-sensitive filenames and byte sizes.

The broader Mindboggle project data page separately describes Mindboggle-101 as v3 (2019-04-03). These appear to be different repository/version namespaces; the relationship is unresolved. This report does not treat Harvard Dataverse v2 as proof that the local set equals OSF v3.

## Results

### Passed

- Raw root exists and contains 24 files totaling 7,984,131,445 bytes.
- All 24 files are represented exactly once in the SHA-256 inventory.
- Every inventory filename, relative path, and byte size matches its current local file.
- Every recorded SHA-256 value is 64 lowercase hexadecimal characters and was reproduced in an independent second hashing pass.
- Against Harvard Dataverse v2: 0 missing filenames, 0 unexpected filenames, 0 byte-size mismatches, and 0 duplicate local filenames.
- `extracted/` contains 0 files; no extraction was performed or detected.

### Missing files

- None relative to the 24-file Harvard Dataverse v2 listing.
- No standalone `LICENSE`, terms-of-use, or changelog file exists among either the local 24 files or the Dataverse v2 file listing. License-notice capture required by the acquisition plan therefore remains unresolved rather than passed.

### Unexpected files

- None relative to the Harvard Dataverse v2 listing.
- Surface-label archives, shape tables, whole-brain label archives, and source code are outside the project's current T1 MRI/manual cortical DKT volume scope, but they are expected members of the authoritative 24-file listing. They remain untouched in raw storage.

### Incorrect or unverified placement

- No semantically incorrect local file placement was observed: archives, metadata, documentation, and source code are separated by category.
- Exact source-directory fidelity is unverified. The Dataverse API supplies empty directory labels for all 24 files, while the local copy uses category subdirectories. The OSF primary-repository hierarchy was not available for comparison. No files were moved to resolve this uncertainty.
- The empty `extracted/` directory is only a placeholder and contains no downloaded or derived files.

## Deferred checks

Archive integrity/content listing, extraction, package-internal paths, scan-level inventory, MRI/label pairing, participant lineage, NIfTI parsing, image/label geometry, intensities, labels, spatial overlap, duplicates, and all quality-control checks were skipped as required by this milestone boundary.
