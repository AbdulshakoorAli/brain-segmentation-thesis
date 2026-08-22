# Mindboggle-101 Acquisition Plan

## Purpose and boundary

Acquire the individual-brains component reproducibly after licensing approval. This plan does not authorize or perform a download, create dataset inventory rows, assign data splits, or implement a loader.

## Preconditions

1. A human reviewer resolves the licensing questions in `docs/dataset_source_and_license.md` for the intended thesis use.
2. The reviewer confirms the exact in-scope package at the OSF primary repository and cross-checks its DOI/collection provenance.
3. Storage capacity, access method, and handling requirements are confirmed without placing credentials in the repository.

## Planned acquisition procedure

1. Create the untracked destination `data/raw/mindboggle-101/`; treat it as immutable source storage.
2. Retrieve only the approved individual-brains package from the recorded authoritative source. Preserve distributed names and directory structure.
3. Record the actual retrieval date, resolved source URL, repository identifier, displayed version, package names, sizes, and cryptographic checksums from observed artifacts.
4. Copy bundled license, citation, changelog, label-definition, subject/source mapping, and provenance notices into the raw snapshot without editing them; reference them from project documentation.
5. Verify archive integrity before extraction. Extract into a separate raw snapshot location without overwriting or renaming source files.
6. Make raw storage read-only where the platform permits. Put all inventories, validation reports, derived files, and caches outside `data/raw/`.
7. Inspect the actual package layout before defining pair-discovery logic. Populate `metadata/scan_manifest.csv` only from source artifacts and authoritative metadata.

## Post-acquisition gates

Acquisition is ready for inventory work only when the source, retrieval date, exact package/version, checksums, raw location, and applicable license notices are recorded. MRI/label parsing, pairing, lineage, shapes, affines, orientations, spacings, intensities, labels, overlap, duplicates, and cohort coverage remain blocked until raw files are present and inspected.

Train/validation/test assignments remain prohibited until participant or acquisition lineage is established. Loader implementation remains prohibited until the package structure and valid MRI/label pairs are known.

## Failure handling

- Do not repair, resample, relabel, or rename raw artifacts.
- Record missing, corrupt, ambiguous, or conflicting artifacts as failures or blockers.
- Stop if licensing is unresolved, package provenance is ambiguous, integrity checks fail, or matching coordinate space cannot later be established.
