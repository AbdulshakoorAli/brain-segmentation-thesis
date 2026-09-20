# Research log: Mindboggle-101 NIfTI read-failure diagnosis

- Date: 2026-09-03
- Skill: repository-local `brain-segmentation-research`
- Initiating request: pause mesh generation and diagnose viewer `ImageFileError: Could not read file` observations in NKI-RS-22, NKI-TRT-20, and OASIS-TRT-20 without assuming invalid scientific pairs.
- Boundaries: read-only raw/archive inspection first; no validation-status changes, exclusion, raw repair, label changes, mesh generation, splits, or training.

## Evidence and result

- Direct NiBabel 5.4.2 loading of the reported NKI-RS-22-1 native MRI and label passed through full voxel materialization.
- The accepted project loader passed all 24 checks for the same pair.
- A 404-file audit across all 202 canonical rows found zero path, existence, regular-file, readability, gzip signature/CRC, NIfTI header, affine, voxel-load, finite-value, accepted-hash, or loader failures.
- The exact MRI and label were streamed from `NKI-RS-22_volumes.tar.gz` into a temporary derived diagnostic location. Archive-member sizes and SHA-256 values matched extracted files, and both temporary copies loaded fully.
- NKI-RS-22, NKI-TRT-20, and OASIS-TRT-20 archives retained accepted inventory hashes.
- Six targeted Streamlit selections across the three named cohorts and two spaces loaded without exceptions or error banners; no mesh directory was created.
- Twelve completed caches remain valid. One pre-existing incomplete MMRR-21-9 build directory was observed and preserved; the resolver ignores it and never supplies it to NiBabel.

NiBabel's exact reported message maps to an `OSError` while opening the file for gzip-signature sniffing. Because all current direct, archive, loader, and application checks pass, the root trigger remains unresolved and is classified as a transient file-open event rather than content corruption or a demonstrated code defect.

## Accounting

- Passed: 404 file audits, 202 loader validations, direct reproduction checks, exact archive comparison, Streamlit integration checks, cache checks, and preservation.
- Failed: none currently reproducible.
- Skipped: mesh generation, raw repair, splits, preprocessing, and model work.
- Unverified: other historical record IDs and the exact OS-level cause.
- Blocked: finer causal attribution requires evidence captured during a recurrence.

No application fix was made and no raw repair is required. Broad mesh generation remains paused for this diagnostic milestone.

