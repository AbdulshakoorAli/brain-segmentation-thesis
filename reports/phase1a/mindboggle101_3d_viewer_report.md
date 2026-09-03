# Manifest-driven Mindboggle-101 on-demand 3D viewer report

Date: 2026-09-02  
Milestone status: **passed**  
Scope: local, read-only visualization of verified MRI/manual-DKT31 pairs; no splitting, preprocessing, training, inference, evaluation, or public deployment.

## Outcome

The general Streamlit viewer supports all 202 verified canonical pairs: Extra-18 36, MMRR-21 42, NKI-RS-22 44, NKI-TRT-20 40, and OASIS-TRT-20 40. The selectable catalog contains exactly 101 native and 101 MNI152 records. The default remains the already cached `MB101:Extra-18:Afterthought-1:native:brain-DKT31` pair.

The displayed labels are **manual DKT31 reference segmentations, not model predictions**.

## Implementation

- `apps/mindboggle101_3d_viewer.py` is the general entry point. It derives cohort, participant, space, and canonical-pair choices only from verified rows in the accepted global manifest.
- `src/brain_segmentation/streamlit_3d_viewer.py` owns the shared application. The Afterthought-specific entry point redirects to it, avoiding divergent implementations.
- `src/brain_segmentation/mesh_cache.py` provides safe hash-based cache names, provenance comparison, stale/incomplete rejection, quarantine of known-invalid caches, and atomic directory publication.
- `src/brain_segmentation/mesh_visualization.py` remains the shared mesh/rendering layer. It now accepts volumes containing any documented subset of DKT IDs, records world bounds, and exposes progress without changing mesh rules.
- The accepted read-only loader and 2D orientation logic were reused unchanged.

No direct dependency changed. The existing NumPy, NiBabel, Matplotlib, scikit-image 0.26.0, Plotly 7.0.0, and Streamlit 1.62.0 environment was sufficient.

## Selection and on-demand behavior

The app resolves each selected `canonical_pair_id` uniquely, loads the pair through the accepted scientific checks, and shows source metadata plus cache status. A valid cache opens immediately. A missing, stale, or incomplete cache does not generate automatically: the local user must press **Generate 3D view**. Progress is reported per observed DKT region. Only the selected pair is generated, outside `data/raw/`, and its validated cache is reused later.

The default Afterthought cache remained compatible and unchanged. New cache directories use `pair-<24 hex characters>`, derived from SHA-256 of the canonical ID; unchecked manifest text never becomes a directory path.

## Cache identity and geometry

Version-2 identity binds the cache to the canonical pair, relative label path, source label SHA-256, complete affine, observed label IDs, dictionary hash, full/display algorithms and parameters, code version, schema version, and mesh level. The manifest is bound by SHA-256 and all array-file hashes are checked. Metadata is written last inside a temporary sibling directory, geometry is validated, and the completed directory is atomically published.

Full-resolution step-1 scientific meshes and reduced step-2 display meshes remain separate. Background 0 is excluded. Every observed foreground region is represented; disconnected components are retained. The complete NIfTI affine is applied once to voxel-coordinate vertices, with no separate spacing multiplication. All representative vertices were finite, all faces triangular and in range, and per-cache world bounds were recorded.

## Ten-record focused validation

Selection was deterministic and covered four available orientation mappings (LAS, RPS, LIA, ASL). Each record contained and meshed 62 foreground regions.

| Cohort | Participant | Space | Orientation | Action | First generation/validation (s) | Cached reload (s) | Regions |
|---|---|---|---|---:|---:|---:|---:|
| Extra-18 | Afterthought-1 | native | LAS | reused | 0.731 | 0.824 | 62 |
| Extra-18 | Afterthought-1 | MNI152 | LAS | generated | 30.305 | 0.678 | 62 |
| MMRR-21 | MMRR-21-10 | native | RPS | generated | 43.493 | 0.662 | 62 |
| MMRR-21 | MMRR-21-10 | MNI152 | LAS | generated | 30.737 | 0.738 | 62 |
| NKI-RS-22 | NKI-RS-22-16 | native | LIA | generated | 63.685 | 0.578 | 62 |
| NKI-RS-22 | NKI-RS-22-16 | MNI152 | LAS | generated | 28.746 | 0.633 | 62 |
| NKI-TRT-20 | NKI-TRT-20-10 | native | LAS | generated | 49.736 | 0.686 | 62 |
| NKI-TRT-20 | NKI-TRT-20-10 | MNI152 | LAS | generated | 30.784 | 0.684 | 62 |
| OASIS-TRT-20 | OASIS-TRT-20-10 | native | ASL | generated | 40.848 | 0.662 | 62 |
| OASIS-TRT-20 | OASIS-TRT-20-10 | MNI152 | LAS | generated | 30.726 | 0.593 | 62 |

For every representative: source loading passed, MRI/label geometry remained compatible, all observed IDs were known and meshed, full/display geometry passed, an independent step-1 affine reconstruction matched cached vertices and faces, left/right and individual-region figures behaved correctly, all three 2D planes rendered, cached reload succeeded, and source hashes were unchanged.

A synthetic identity mismatch was rejected as stale. A synthetic manifest-only cache was classified incomplete and moved to a rejected evidence directory without touching an accepted cache. Repeating generation for the non-default Extra-18 MNI152 record produced byte-identical mesh files.

## Application and launcher checks

The app retains orbit rotation, zoom, pan/modebar reset, explicit camera reset, opacity, show/hide all, individual selection, search, hemisphere filters, deterministic colors, DKT hover metadata, and accepted three-plane 2D controls. Errors are shown in the application without terminating the selector workflow.

Streamlit AppTest changed cohort, participant, and space from the default to MMRR-21 / MMRR-21-10 / MNI152 with zero exceptions. The local health endpoint returned HTTP 200 and `ok`. The generic launcher validation passed.

Launch from the repository root:

```powershell
.\launch_mindboggle101_3d_viewer.cmd
```

Equivalent command:

```powershell
.venv\Scripts\python.exe -m streamlit run apps\mindboggle101_3d_viewer.py --server.address 127.0.0.1
```

## Screenshots

Eight representative PNGs are under `reports/phase1a/screenshots/mindboggle101_3d_viewer/`: default Afterthought, selectors, non-Extra native, MNI152, left hemisphere, right hemisphere, individual region, and combined 2D/3D.

## Preservation and limitations

Before/after bundle hashes matched for 14 raw archives, 7 cohort/global manifests, 12 accepted QC CSVs, 12 lineage/overlap CSVs, the DKT dictionary, accepted loader/2D code, and all 249 legacy Afterthought cache files. The ten representative caches occupy 317,199,423 bytes (about 302.5 MiB); 289,782,852 bytes are the nine new generic caches. First generation is CPU- and storage-intensive. Only ten records are cached; the other 192 generate solely after selection.

Licensing reconciliation, Dataverse v2 versus OSF v3 equivalence, NKI acquisition uncertainties, OASIS external overlap, and historical label-notice scope remain unresolved. This technical milestone does not establish clinical validity, does not substitute for professor review on the target display/browser/GPU, and does not complete Phase 1A.

## Accounting

- Passed: 202-ID selector resolution; eligibility filtering; ten source/mesh/affine/control/cache validations; stale and incomplete scenarios; non-default determinism; app interaction; HTTP health; launcher; 8/8 existing tests; preservation.
- Failed: none.
- Skipped: mesh generation for the remaining 192 records; exhaustive browser/device review; splits and all model work.
- Unverified: professor usability on the actual presentation computer and scientific claims beyond source-faithful display.
- Blocked: licensing/provenance reconciliation and Phase transition remain human-review decisions.

The manifest-driven, on-demand Mindboggle-101 3D viewer passes this scoped milestone and is ready for a local professor demonstration.

Exact next recommended task: launch the general viewer for a bounded professor walkthrough using the cached default and one cross-cohort/native-or-MNI selection, then record the professor's usability and scientific-display feedback without generating splits or claiming Phase 1A complete.

