# Extra-18 Phase 1A NIfTI Pair QC Report

## Scope and checkpoint result

Extra-18 passes this Phase 1A NIfTI header and voxel-level QC checkpoint. All 36 canonical MRI/manual-DKT31 pairs are verified: 18 native-space pairs and 18 MNI152-space pairs. No pair failed or was blocked.

This result applies only to rows in `data/derived/manifests/extra18_scan_inventory.csv`. Full-head T1 volumes and `manual+aseg` volumes were not processed as canonical inputs. No other cohort was processed. No file was resampled, normalized, reoriented, cropped, repaired, or otherwise modified.

Phase 1A as a whole is not complete: other cohorts, participant/acquisition lineage, leakage-safe splits, and the loader remain outstanding. Licensing and Harvard Dataverse v2 versus OSF/project v3 equivalence remain unresolved for human review.

## Method

- Code: `src/brain_segmentation/qc.py` and `scripts/run_extra18_qc.py`.
- NIfTI parser: NiBabel 5.4.2; numerical operations: NumPy 2.5.2.
- Pair geometry: both inputs must be 3D and have exactly equal shapes.
- Affines: finite 4x4 matrices compared with `numpy.allclose`, `rtol=1e-5`, `atol=1e-5`; tolerances are in every QC row. Maximum observed elementwise absolute difference was `7.62939453125e-06`.
- Orientation: NiBabel axis codes must match within each pair; codes are recorded, not standardized.
- Spacing: three finite, positive values must match within the same tolerances.
- Space consistency: manifest value, distributed filenames, shape, affine, orientation, and spacing must agree. This verifies within-pair/file-declared space, not independent template provenance.
- MRI content: all values finite, at least one nonzero voxel, and observed maximum greater than minimum. No clinical threshold was introduced.
- Labels: all values finite and exactly integer-valued. Every nonzero anatomical ID must occur in the distributed `cortex_numbers_names` block. Voxel `0` is treated as unlabeled background and is not invented as a dictionary row.
- Segmentation: at least one nonzero label voxel.
- Spatial overlap: at least one segmentation voxel must intersect finite, nonzero support in the skull-stripped MRI. Counts and overlap fraction are recorded. This is a technical alignment check, not clinical validation.
- Duplicates: SHA-256 for each compressed canonical file and decoded voxel array (including shape and dtype), plus whole-pair voxel duplicate grouping.

## Observed results

All 36 pairs passed parsing, dimensional compatibility, affine compatibility, orientation matching, spacing matching, declared-space consistency, finite values, MRI content/variation, label integrality, segmentation nonemptiness, label vocabulary, spatial overlap, and duplicate-analysis completion.

Observed shape groups:

- MNI152: 18 at `182x218x182`.
- Native: 3 at `176x256x256`, 1 at `181x217x181`, 12 at `256x256x170`, and 2 at `256x256x256`.

Observed orientation groups:

- MNI152: 18 `LAS`.
- Native: 3 `LAS`, 1 `RAS`, 12 `PIR`, and 2 `LIA`.

Observed spacing groups:

- MNI152: 18 at `1;1;1`.
- Native: 15 at `1;1;1`; three had first-axis zooms `0.999997139`, `0.999997735`, and `0.999998033`, with `1;1` on the other axes. MRI and label spacing matched within every pair.

Every label volume contained background `0` plus all 62 DKT cortical IDs parsed from `label_definitions.txt`. Unknown anatomical label IDs: none. Segmentation overlap fractions ranged from `0.999974524511` to `1.0`. No exact compressed-file, decoded MRI, decoded label, or whole-pair voxel duplicate was found.

## Artifacts and reproducibility

- `data/derived/qc/extra18_pair_qc.csv`: 36 rows.
- `data/derived/qc/extra18_failures.csv`: header plus 0 rows.
- `data/derived/dictionaries/dkt_label_dictionary.csv`: 62 rows; original IDs preserved; class indices blank.
- `data/derived/manifests/extra18_scan_inventory.csv`: 36 rows, all `verified`.

Automated tests ran twice and passed 8/8 both times. Full QC ran twice and reported 36 verified, 0 failed, 0 blocked both times. Generated CSVs were byte-identical:

- Pair QC: `c7bee67f1226753b2683ebdd5c5222a000d7f5e982ebe09d9272722ae38ca3f5`.
- Failures: `6439a730c7d63f2a588757b7d5a55cb244ef879745f17709022ec0399d7dbda7`.
- DKT dictionary: `76a113acec22cad1ec1fcb67fedc7f2b3d6a8eafe6e53ca6c5873e8a64651306`.
- Manifest: `f6018f27e385cb803f4e56239a0d4ca4ed60df8c08d6b7045984363f8db1def7`.

The post-QC source archive SHA-256 remains `89e5d9a635fb12227e3c132d33ecb15aeeaeb54a7db02ad29ecfa7085468eb9c`, exactly matching `metadata/raw_file_inventory.csv`. QC only read canonical NIfTIs and wrote outside `data/raw/`.

## Final accounting

### Passed

- 36/36 canonical pairs; 18 native and 18 MNI152.
- All required check categories for every pair.
- 8/8 automated tests on each of two runs.
- Byte-identical artifacts from two QC runs.

### Failed

- None.

### Skipped

- Full-head T1 and `manual+aseg` auxiliary files.
- Every cohort other than Extra-18.
- Splits, loader, training code, and visualization.

### Unverified

- Harvard Dataverse v2 versus OSF/project v3 equivalence.
- Participant/acquisition lineage beyond supplied identifiers/source fields.
- Template provenance beyond distributed MNI152 filenames and within-pair geometry.
- Scientific or clinical validity.

### Blocked

- Package/component licensing reconciliation requires human review.
- Broader Phase 1A completion awaits remaining cohorts, lineage-safe splitting, and later loader validation.

- Native verified-pair count: 18.
- MNI152 verified-pair count: 18.
- Subjects requiring investigation from this technical QC: none.
- Unknown label IDs: none.
- Exact next recommended task: human-review this Extra-18 checkpoint and unresolved provenance/licensing notes, then explicitly authorize and scope the next single Phase 1A cohort inventory/QC milestone; do not create splits until participant/acquisition lineage is resolved.

