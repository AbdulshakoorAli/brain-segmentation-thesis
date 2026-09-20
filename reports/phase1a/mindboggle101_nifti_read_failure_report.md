# Mindboggle-101 NIfTI read-failure diagnosis

Date: 2026-09-03  
Scope: read-only diagnosis of the manifest-driven viewer; mesh generation remained paused.

## Outcome

No current NIfTI failure was reproducible. All 404 MRI/label file references from the 202 verified canonical rows passed path resolution, regular-file/readability checks, gzip signature and complete CRC-checked decompression, NiBabel header and affine access, complete voxel-array loading, finite-value checks, accepted-QC hash comparison, and the accepted project loader.

The one exactly identified observation was:

- `MB101:NKI-RS-22:NKI-RS-22-1:native:brain-DKT31`
- MRI: `data/raw/mindboggle101/extracted/NKI-RS-22/NKI-RS-22_volumes/NKI-RS-22-1/t1weighted_brain.nii.gz`
- Label: `data/raw/mindboggle101/extracted/NKI-RS-22/NKI-RS-22_volumes/NKI-RS-22-1/labels.DKT31.manual.nii.gz`
- Reported exception: `nibabel.filebasedimages.ImageFileError: Could not read file: .../t1weighted_brain.nii.gz`

Additional exact pair identifiers were not supplied for the similar NKI-RS-22, NKI-TRT-20, and OASIS-TRT-20 observations, so their historical count remains unverified. Current affected records are zero in every cohort and space; neither MRI nor label currently fails.

## Exact failure-stage interpretation

In installed NiBabel 5.4.2, the exact text `Could not read file` is produced by `_signature_matches_extension()` when Python `open(filename, 'rb')` raises `OSError` during compressed-file signature sniffing. It is distinct from NiBabel's messages for an empty file, wrong gzip signature, or unrecognized image type.

Therefore, the historical event localizes to **file open**, before gzip decompression and NIfTI parsing. Its underlying OS cause is unresolved. A transient permissions/file-lock or system-resource event is compatible with the message, but none was reproduced and no specific one is claimed.

## NKI-RS-22-1 direct and loader results

The manifest strings had no leading/trailing whitespace or invisible characters and resolved inside the expected extracted-data root.

| File | Size | SHA-256 | Gzip/CRC | NiBabel header/voxels |
|---|---:|---|---|---|
| Native MRI | 1,938,614 | `422c7d26c26f79522190d82d2e9e5030cdd0fb8a6bf1912770925ffde1dc8edc` | passed; 50,332,000 decompressed bytes | passed; `192x256x256`, finite |
| Native label | 650,696 | `19f760e2c3b2a90d36c47e772c1a99475d6704a3ba37e6ab4ae296b42a2773c9` | passed; 50,332,000 decompressed bytes | passed; `192x256x256`, finite |

The accepted project loader passed all 24 checks for the pair. The current hashes exactly match the original NKI-RS-22 QC evidence.

## Extracted-versus-archive comparison

`NKI-RS-22_volumes.tar.gz` remains 924,552,880 bytes with accepted SHA-256 `450588dcb8528b617c1472cb8119748f60481b6d40d2d10e6aafca21a8e078c4`.

The extracted MRI and label match their exact archive members in name, byte size, and SHA-256. Each member was streamed to a temporary diagnostic directory outside raw storage and independently passed gzip, NiBabel header/affine, and full voxel loading. The temporary directory was removed after the check. NKI-TRT-20 and OASIS-TRT-20 archives also retain their accepted inventory hashes.

No extracted/archive mismatch exists and no raw-file repair is required or proposed.

## Application and cache investigation

Streamlit AppTest selected native and MNI152 records for NKI-RS-22-1, NKI-TRT-20-1, and OASIS-TRT-20-1. All six loaded with zero exceptions and zero error banners. The primary mesh-directory set was unchanged before and after.

The viewer does not cache loaded NIfTI pairs or exceptions with Streamlit resource/data decorators. Path conversion is identical to direct loader use. Cache artifacts are not examined until after source-pair loading and are never passed to NiBabel.

Twelve completed mesh caches passed their provenance and geometry checks against current source labels. One previously interrupted MMRR-21-9 `.building-28612` directory is present without a completion manifest; it is ignored by the cache resolver, was not treated as NIfTI, and was preserved unchanged. No active Python or Streamlit process remained after reproduction.

## Classification

- Incorrect manifest path: ruled out.
- Missing, zero-byte, truncated, invalid-gzip, or invalid-NIfTI file: ruled out by all-file audit.
- Extracted/archive mismatch or invalid archive member: ruled out for the exact reported pair.
- Current loader/application bug: not reproduced; targeted application selections passed.
- Permissions/file-lock/resource event: possible but not proven.
- Final classification: **unresolved transient file-open failure**.

No application or loader change was made because there is no evidence-supported defect to correct. Automatic retry was deliberately not added because it could hide a persistent corruption or permissions error.

## Accounting

- Passed: 404/404 files, 202/202 loader pairs, direct NKI-RS-22-1 load, exact archive comparison, six targeted Streamlit selections, three archive inventory hashes, and 12 completed-cache validations.
- Failed: 0 current files and 0 current canonical records.
- Skipped: mesh generation/regeneration, destructive lock manipulation, raw repair, splits, and training.
- Unverified: exact identities of other historically observed failures and the OS-level trigger for the transient `open()` failure.
- Blocked: a more specific causal diagnosis requires recurrence-time OS/file-lock/resource evidence.

Raw files, manifests, validation statuses, dictionaries, and caches were not modified. The audit CSV and diagnosis JSON are derived evidence only.

Exact next recommended action: close any old viewer/terminal processes, relaunch the local viewer, and select NKI-RS-22-1 native without generating a mesh. If the error recurs, capture the timestamp, full chained exception, active processes/file locks, and system memory/handle state before any repair is considered.

