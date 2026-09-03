# Brain Segmentation Research State

## Project

- Objective: Build a reproducible foundation for brain MRI segmentation research using Mindboggle-101 T1 MRI and manual DKT cortical labels.
- Dataset and version: Mindboggle-101 individual brains; 24 local files match the Harvard Dataverse v2 filename/size listing, while the project page reports OSF/project v3 (2019-04-03); equivalence is unverified.
- Current phase: Phase 1A — Dataset foundation and visualization pre-MVP.
- Current milestone: The interactive 3D professor-demonstration MVP for the accepted Extra-18 `Afterthought-1` native MRI/manual-DKT31 pair passes scoped technical validation and awaits professor review; split policy, preprocessing, and training remain explicitly deferred.
- Last updated: 2026-08-31.

## Completed

- 2026-09-02 — Manifest-driven, on-demand Mindboggle-101 3D viewer passed its scoped technical milestone: all 202 verified canonical IDs are selectable, exactly 10 representative pair caches were generated/reused, and the remaining 192 records stay on-demand only.
- General Streamlit application and cache layer created — `apps/mindboggle101_3d_viewer.py`, `src/brain_segmentation/streamlit_3d_viewer.py`, `src/brain_segmentation/mesh_cache.py`, and `launch_mindboggle101_3d_viewer.cmd`.
- The original Afterthought entry point and launcher now redirect compatibly to the shared general implementation; the 249-file accepted Afterthought cache remains unchanged and opens immediately.
- All ten representatives passed source validation, 62/62 foreground-region mesh coverage, finite/valid geometry, independent affine checks, hemisphere/region controls, three-plane rendering, and cached reload; stale, incomplete, deterministic-repeat, app-health, launcher, and preservation checks passed.
- Validation evidence, report, log, and eight screenshots created under `data/derived/qc/`, `reports/phase1a/`, and `research_log/`.

- Repository instructions created — `AGENTS.md`.
- Source, scope, upstream version status, and licensing questions recorded — `docs/dataset_source_and_license.md`.
- No-download acquisition procedure recorded — `docs/acquisition_plan.md`.
- Header-only proposed schemas created — `metadata/scan_manifest.csv`, `metadata/manifest_data_dictionary.csv`, and `metadata/dkt_label_dictionary.csv`.
- Raw-file inventory created — `metadata/raw_file_inventory.csv` covers all 24 downloaded files with relative path, filename, byte size, and SHA-256.
- Raw organization assessed — `docs/raw_dataset_organization_report.md`; no missing or unexpected files against Harvard Dataverse v2.
- Prompt and validation evidence recorded — `research_log/phase-1a-initiation.md`, `research_log/phase-1a-raw-inventory.md`, `research_log/phase-1a-extra18.md`, and `research_log/phase-1a-extra18-qc.md`.
- Extra-18 archive checksum, gzip/tar integrity, member-path safety, and extraction validated; source archive unchanged and 183 safe members extracted.
- Exact Extra-18 extracted structure recorded — `data/derived/manifests/extra18_extracted_structure.txt` contains 19 directories and 164 files.
- Extra-18 candidate manifest created and QC-updated — `data/derived/manifests/extra18_scan_inventory.csv` contains 18 native and 18 MNI152 canonical pairs, all `verified`.
- Reproducible inventory and QC code created — `scripts/inventory_extra18.ps1`, `src/brain_segmentation/qc.py`, and `scripts/run_extra18_qc.py`.
- Automated QC tests created — `tests/test_qc.py` covers valid input, shape mismatch, affine mismatch, non-finite MRI and label values, non-integer labels, empty segmentation, and unknown label IDs.
- DKT dictionary derived from the distributed cortical definition block — `data/derived/dictionaries/dkt_label_dictionary.csv` contains 62 original IDs; class indices remain blank.
- Pair QC and failure artifacts created — `data/derived/qc/extra18_pair_qc.csv` contains 36 verified rows and `data/derived/qc/extra18_failures.csv` contains 0 failure rows.
- QC report created — `reports/phase1a/extra18_qc_report.md`.
- MMRR-21 archive safely extracted and exactly reconciled — 211 members match 211 disk entries under `data/raw/mindboggle101/extracted/MMRR-21/`.
- MMRR-21 inventory and lineage evidence recorded — `data/derived/manifests/mmrr21_scan_inventory.csv` contains 21 native and 21 MNI152 canonical rows, all technically verified; supplied repeat mapping is present for subjects 1–10 only.
- MMRR-21 pair QC completed — `data/derived/qc/mmrr21_pair_qc.csv` contains 42 verified rows and `data/derived/qc/mmrr21_failures.csv` contains 0 failure rows.
- MMRR-21 orchestration, report, and prompt/validation evidence created — `scripts/inventory_mmrr21.py`, `scripts/run_mmrr21_qc.py`, `reports/phase1a/mmrr21_qc_report.md`, and `research_log/phase-1a-mmrr21-qc.md`.

- MMRR-21 evidence-based lineage table created — `data/derived/metadata/mmrr21_lineage.csv` contains 42 scan records mapped to 21 participant groups and 21 repeat-acquisition groups.
- MMRR-21 historical label notices reconciled — `data/derived/metadata/mmrr21_label_issue_review.csv` contains six annotation-only entries across five subjects, with zero supported exclusions.
- MMRR-21 lineage report, reusable review script, and research log created — `reports/phase1a/mmrr21_lineage_review.md`, `scripts/review_mmrr21_metadata.py`, and `research_log/phase-1a-mmrr21-lineage.md`.
- NKI-RS-22 archive safely extracted and exactly reconciled — 221 safe members match 221 disk entries under `data/raw/mindboggle101/extracted/NKI-RS-22/`.
- NKI-RS-22 inventory and pair QC completed — `data/derived/manifests/nki_rs22_scan_inventory.csv` and `data/derived/qc/nki_rs22_pair_qc.csv` contain 22 native and 22 MNI152 canonical rows, all verified; the failure table is empty.
- NKI-RS-22 lineage and label review completed — `data/derived/metadata/nki_rs22_lineage.csv` resolves 22 participant groups and records one ambiguous acquisition session; `data/derived/metadata/nki_rs22_label_issue_review.csv` reconciles 18 issue-ID entries.
- Parameterized archive/inventory and QC runners created — `scripts/inventory_mindboggle_volume_cohort.py` and `scripts/run_cohort_qc.py`; accepted QC rules remain unchanged.
- NKI-RS-22 report and prompt/validation log created — `reports/phase1a/nki_rs22_qc_report.md` and `research_log/phase-1a-nki-rs22-qc.md`.
- NKI-TRT-20 archive safely extracted and exactly reconciled — 201 safe members match 201 disk entries under `data/raw/mindboggle101/extracted/NKI-TRT-20/`.
- NKI-TRT-20 inventory and pair QC completed — 20 native and 20 MNI152 canonical pairs are verified in `nki_trt20_scan_inventory.csv` and `nki_trt20_pair_qc.csv`; failures are empty.
- NKI-TRT-20 lineage and label review completed — 20 participant/test-retest groups recorded with acquisition roles unresolved; 397 historical issue-ID records classified with zero exclusions.
- NKI cross-cohort overlap review created — `data/derived/metadata/nki_cross_cohort_overlap_review.csv` confirms two shared NKI-RS/NKI-TRT participants and records wider external-NKI evidence.
- NKI-TRT-20 report, reusable metadata generator, and research log created — `reports/phase1a/nki_trt20_qc_report.md`, `scripts/review_nki_trt20_metadata.py`, and `research_log/phase-1a-nki-trt20-qc.md`.
- OASIS-TRT-20 archive safely extracted and exactly reconciled — 201 safe members match 201 disk entries under `data/raw/mindboggle101/extracted/OASIS-TRT-20/`.
- OASIS-TRT-20 inventory and pair QC completed — 20 native and 20 MNI152 canonical pairs are verified; the failure table is empty.
- OASIS-TRT-20 lineage and overlap review completed — 20 participant/repeat groups, 18 included tests, two included retests, and all external counterpart sessions are resolved; all 20 overlap the OASIS-1 reliability release.
- OASIS-TRT-20 label review completed — nine historical pole-ID records across eight subjects are annotation-only with zero exclusions.
- OASIS-TRT-20 report, reusable metadata generator, and research log created — `reports/phase1a/oasis_trt20_qc_report.md`, `scripts/review_oasis_trt20_metadata.py`, and `research_log/phase-1a-oasis-trt20-qc.md`.
- Reusable global consolidation created — `scripts/build_mindboggle101_global_manifest.py` explicitly reconciles the five accepted inventory/QC schemas without modifying source artifacts.
- Global scan-space and subject manifests created — `data/derived/manifests/mindboggle101_scan_manifest.csv` contains 202 verified canonical pairs and `data/derived/manifests/mindboggle101_subject_manifest.csv` contains 101 included subject/acquisition records.
- Global participant and overlap tables created — `data/derived/metadata/mindboggle101_participant_groups.csv` and `mindboggle101_global_overlap_review.csv` contain 99 evidence-derived groups, including two confirmed shared NKI cross-cohort groups.
- Global manifest dictionary and audit created — the 40-field dictionary defines every scan-manifest field; `mindboggle101_manifest_audit.csv` records 26 passed, 0 failed, 4 unverified, and 1 blocked check, while the failure table is empty.
- Global report and prompt/validation log created — `reports/phase1a/mindboggle101_global_manifest_report.md` and `research_log/phase-1a-global-manifest.md`.
- Minimal read-only canonical-pair loader created — `src/brain_segmentation/loading.py` selects verified manifest rows and validates real NIfTI pairs without transforms or source writes.
- Reusable orthogonal manual-DKT31 viewer created — `src/brain_segmentation/visualization.py` keeps visualization separate from loading and provides axial/coronal/sagittal MRI, label-only, and overlay views with slice, opacity, mode, anatomical-label, and label-ID/name controls.
- Deterministic Extra-18 visualization runner created — `scripts/run_extra18_visualization.py` selects `MB101:Extra-18:Afterthought-1:native:brain-DKT31`, validates it, exercises controls, and writes machine-readable evidence and four screenshots.
- Extra-18 visualization report and research record created — `reports/phase1a/extra18_visualization_report.md` and `research_log/phase-1a-extra18-visualization.md`.
- Representative screenshots created under `reports/phase1a/screenshots/extra18_visualization/` for axial, coronal, sagittal, and combined three-plane overlays.
- Visualization dependency record created — `requirements-visualization.txt` reuses accepted QC dependencies and adds only Matplotlib `3.10.7` directly.
- Manifest-driven viewer created — `scripts/run_mindboggle101_viewer.py` provides cascading cohort, participant/scan, coordinate-space, and canonical-pair selectors populated from the accepted global manifest.
- Reusable loader generalized without replacement — `src/brain_segmentation/loading.py` now resolves all verified rows by `canonical_pair_id` and validates native or MNI152 products using the accepted scientific checks.
- Anatomical-plane handling generalized — `src/brain_segmentation/visualization.py` derives axial/coronal/sagittal axes from each record's orientation metadata without reorienting source arrays; all six observed orientation codes are supported.
- Mindboggle viewer smoke evidence created — `data/derived/qc/mindboggle101_viewer_smoke_validation.json` records exactly one deterministic native and MNI152 pair per cohort, 10 passed and 0 failed.
- Manifest-driven viewer report and research record created — `reports/phase1a/mindboggle101_viewer_report.md` and `research_log/phase-1a-mindboggle101-viewer.md`.
- Focused visual-acceptance evidence created — `data/derived/qc/mindboggle101_visual_acceptance.json`, `reports/phase1a/mindboggle101_visual_acceptance_report.md`, and `research_log/phase-1a-visual-acceptance.md`.
- Afterthought-1 diagnostics created — MRI-only, label-only, overlay, and five-nearby-slice screenshots plus three required combined usability screenshots under `reports/phase1a/screenshots/visual_acceptance/`.
- Reproducible acceptance runner created — `scripts/run_mindboggle101_visual_acceptance.py` measures source support and display transforms without changing the accepted loader/viewer or NIfTI inputs.
- Participant-grouped split-policy proposal created — `reports/phase1a/mindboggle101_split_policy_proposal.md` documents the evidence, proposed 70/15/16 subject-record targets, cohort-balance targets, group-integrity hierarchy, seed, external-overlap constraints, and required future audit without assigning any split.
- Split-policy initiating prompt and evidence recorded — `research_log/phase-1a-split-policy-review.md`.
- Single-record 3D mesh/rendering support created — `src/brain_segmentation/mesh_visualization.py` derives original-ID manual-DKT31 surfaces and reuses accepted 2D orientation logic without changing source arrays.
- Local Streamlit professor demo created — `apps/afterthought1_3d_professor_demo.py` provides orbit/zoom, hemisphere, region, opacity, slice, display-mode, metadata, label-name, and manual-reference controls for Afterthought-1 native only.
- Derived Afterthought-1 meshes created — 62 regions, 608,797 full-resolution vertices, 1,237,714 full-resolution faces, and coherent step-2 display surfaces under `data/derived/visualization/afterthought1_native_dkt31_meshes/`.
- Windows one-click launcher created and validated — `launch_afterthought1_3d_demo.cmd` starts the local Streamlit application from the project virtual environment.
- Professor-demo build, validation, report, and research record created — `scripts/build_afterthought1_3d_professor_demo.py`, `scripts/validate_afterthought1_3d_professor_demo.py`, `data/derived/qc/afterthought1_3d_demo_validation.json`, `reports/phase1a/afterthought1_3d_professor_demo_report.md`, and `research_log/phase-1a-afterthought1-3d-professor-demo.md`.
- Five representative professor-demo screenshots created under `reports/phase1a/screenshots/afterthought1_3d_professor_demo/`.

## In progress

- Professor visual/usability review of the technically validated all-record local viewer is pending. Phase 1A is not complete.

## Blocked

- Package/version provenance — the local set matches Harvard Dataverse v2 by filename and size, but its relationship to the OSF/project-level v3 designation is unverified.
- Package/component license reconciliation — no standalone license notice is present in the local or Dataverse v2 24-file listing; human review is required.
- Source-directory fidelity — Dataverse supplies no directory labels and the OSF hierarchy was unavailable, so the local category-folder layout cannot be proven identical to the acquisition source.
- NKI participant grouping is resolved, but NKI acquisition/session roles and exact cross-cohort acquisition relationships remain unverified; OASIS-2/OASIS-3 row-level overlap is also unverified.
- Leakage-safe train/validation/test assignments — participant grouping evidence is available, but generation awaits explicit human approval of the proposed scientific policy.

## Decisions

- 2026-08-22 — Initially planned `data/raw/mindboggle-101/` as immutable storage; superseded by the observed user-specified `data/raw/mindboggle101/` path.
- 2026-08-22 — Leave proposed CSV schemas header-only to avoid inventing participants, files, label IDs, or validation outcomes.
- 2026-08-22 — Treat licensing as unresolved pending qualified human review.
- 2026-08-23 — Use `data/raw/mindboggle101/` as the observed immutable raw root; do not rename or move raw files.
- 2026-08-23 — Treat Harvard Dataverse v2 and OSF/project v3 as distinct unresolved designations; matching filenames/sizes do not prove equivalence.
- 2026-08-23 — Inventory every downloaded file, including out-of-scope components, without deleting or filtering raw data.
- 2026-08-23 — Extract only `Extra-18_volumes.tar.gz` after checksum, integrity, path-safety, and entry-type checks passed.
- 2026-08-23 — Use skull-stripped `t1weighted_brain` plus `labels.DKT31.manual` as the canonical pair; retain full-head T1 and `manual+aseg` as auxiliary.
- 2026-08-26 — Treat voxel value `0` as unlabeled background and do not invent a dictionary row; validate every nonzero anatomical ID against the distributed 62-row cortical DKT block.
- 2026-08-26 — Require exact 3D shape equality and compare pair affines/spacings with `rtol=1e-5`, `atol=1e-5`; record tolerances and evidence.
- 2026-08-26 — Define technical overlap as at least one nonzero segmentation voxel intersecting finite, nonzero support in its skull-stripped MRI; record counts/fractions and make no clinical-validity claim.
- 2026-08-26 — Accept all 36 Extra-18 canonical pairs as `verified` after every required check passed twice with deterministic artifacts; this does not complete Phase 1A or resolve licensing/provenance.
- 2026-08-26 — Accept all 42 MMRR-21 canonical pairs as technically `verified` using the unchanged QC implementation and existing DKT dictionary after two deterministic runs.
- 2026-08-26 — Preserve supplied MMRR-21 Visit IDs, scan-information SubjectIDs, and repeat-mapping strings verbatim; do not infer repeat status where the supplied repeat table has no row.
- 2026-08-26 — Record the five MMRR-21 label-issue notices as provenance follow-up because their cited IDs were absent from canonical voxel data; do not add unobserved IDs to the DKT dictionary.

- 2026-08-27 — Group MMRR-21 scans by the three-digit SubjectID supported by the README and complete 42-session demographics table; keep native/MNI152 products and any future counterpart-session derivative in the same participant group.
- 2026-08-27 — Preserve MMRR temporal scan/rescan role as unresolved because session IDs were randomized; do not infer role from numbering.
- 2026-08-27 — Treat all six March 2019 MMRR issue-ID entries as annotation-only for current canonical data, with zero exclusions; retain exact product scope as unresolved and keep unobserved IDs out of the voxel dictionary.
- 2026-08-27 — Accept all 44 NKI-RS-22 canonical pairs after two deterministic runs of the unchanged QC implementation; retain full-head T1 and manual+aseg as auxiliary.
- 2026-08-27 — Use unique `NKI_Rockland_<number>` source identifiers as evidence-supported NKI participant groups; keep native/MNI152 products together.
- 2026-08-27 — Leave the `NKI-RS-22-16` acquisition session unresolved because selected-22 and MRI-QC tables disagree; do not infer between `MR_3927656_3303` and `MR_3927656_3268`.
- 2026-08-27 — Classify seven NKI temporal-pole issue entries as annotation-only and eleven non-DKT31 entries as not applicable to canonical manual DKT31; support no exclusions and add no metadata-only IDs to the voxel dictionary.
- 2026-08-27 — Accept all 40 NKI-TRT-20 canonical pairs after two deterministic runs of the unchanged QC implementation and dictionary.
- 2026-08-27 — Treat all 20 NKI-TRT source subjects as confirmed participant and study-design repeat groups, while leaving included/counterpart sessions and scan/rescan roles unresolved.
- 2026-08-27 — Assign shared participant groups to NKI-TRT-20-5/NKI-RS-22-3 (1427581) and NKI-TRT-20-14/NKI-RS-22-14 (3808535); absence of voxel duplicates does not resolve acquisition identity.
- 2026-08-27 — Classify 12 NKI-TRT temporal-pole issue records as annotation-only and 385 other metadata IDs as not applicable to canonical DKT31; support zero exclusions.
- 2026-08-27 — Accept all 40 OASIS-TRT-20 canonical pairs after two deterministic runs of the unchanged QC implementation and dictionary.
- 2026-08-27 — Group OASIS scans by `OAS1_<number>` participant identity; preserve explicit MR1 test/MR2 retest roles and counterpart sessions from the supplied reliability README.
- 2026-08-27 — Record all 20 OASIS participants as external OASIS-1 reliability overlaps, with no other Mindboggle participant or exact canonical file/voxel overlap observed.
- 2026-08-27 — Treat nine OASIS pole-ID issue records as annotation-only for current canonical data; support zero exclusions and retain exact product scope as unresolved.
- 2026-08-27 — Accept the consolidated global manifest with 101 subject/acquisition records, 202 verified scan-space pairs, and 99 evidence-derived participant groups.
- 2026-08-27 — Preserve `NKI-Rockland-1427581` and `NKI-Rockland-3808535` as the two shared cross-cohort groups; retain the exact acquisition relationships as unresolved.
- 2026-08-27 — Encode 61 future grouping constraints (21 MMRR, 20 NKI-TRT, and 20 OASIS) and require native/MNI152 products from each included acquisition to remain together.
- 2026-08-27 — Treat unresolved external-dataset overlap, historical label-product scope, package-version equivalence, and licensing as provenance constraints rather than internal technical-QC failures.
- 2026-08-30 — Move directly to the Extra-18 visualization pre-MVP without a separate loader-testing milestone; implement only the read-only loading required for the selected real pair.
- 2026-08-30 — Select `MB101:Extra-18:Afterthought-1:native:brain-DKT31` deterministically as the minimum `(canonical_pair_id, scan_id)` among verified included Extra-18 native rows.
- 2026-08-30 — Choose initial sagittal/coronal/axial slices `89/121/159` as the integer center of the nonzero manual-segmentation extent; do not choose slices by appearance.
- 2026-08-30 — Use original MRI values and DKT IDs without preprocessing; use a separate display-only deterministic color index with transparent background.
- 2026-08-30 — Add Matplotlib `3.10.7` as the only direct visualization dependency and retain the existing NumPy/NiBabel versions.
- 2026-08-30 — Generalize the accepted loader/viewer rather than replacing them; preserve the Extra-18 runner as a compatible specialized entry point.
- 2026-08-30 — Resolve displayed records by unique `canonical_pair_id` from the global manifest and populate selector choices from observed manifest values rather than hard-coded cohort/subject/path metadata.
- 2026-08-30 — Define anatomical planes from each observed NIfTI orientation (`ASL`, `LAS`, `LIA`, `PIR`, `RAS`, `RPS`) while retaining the original voxel array and affine unchanged.
- 2026-08-30 — Limit practical general-viewer validation to exactly 10 records: the deterministic minimum canonical pair in native and MNI152 space for every observed cohort.
- 2026-08-30 — Add no dependency for the general viewer; reuse existing Matplotlib and standard-library Tk 8.6.
- 2026-08-30 — Attribute the Afterthought-1 slice-89 appearance to the distributed source pair: MRI/label transforms are identical, every labeled voxel has nonzero moderate-intensity MRI support, and fragmentation exists in the original arrays.
- 2026-08-30 — Make no visualization correction because no display bug was observed; retain the accepted viewer and earlier screenshots unchanged.
- 2026-08-30 — Accept focused human usability using exactly Afterthought-1 native LAS, deterministic Colin27-1 native RAS, and deterministic Afterthought-1 MNI152 LAS evidence, while documenting source-display heterogeneity.
- 2026-08-31 — Do not approve or generate dataset splits; defer the proposed 70/15/16 targets, cohort matrix, seed, tie-breaking, and coordinate-space policy until after professor visualization review.
- 2026-08-31 — Make the single-record Afterthought-1 native Streamlit 3D professor demonstration the active milestone; preprocessing, training, inference, evaluation, and meshes for the other 201 records remain out of scope.
- 2026-08-31 — Add Streamlit 1.62.0, Plotly 7.0.0, and scikit-image 0.26.0 as the only direct 3D-demo dependencies; retain the accepted NumPy, NiBabel, Pytest, and Matplotlib pins.
- 2026-08-31 — Preserve full step-1 marching-cubes meshes and use coherent step-2 derived display meshes for browser responsiveness; background remains unmeshed and all vertices use the accepted native affine.
- 2026-08-31 — Treat all displayed DKT31 surfaces as manual reference derivatives, never model predictions or clinical surfaces.
- 2026-09-02 — Support all 202 verified pairs through manifest-derived selectors, but generate meshes only after explicit local user action; retain exactly ten representative caches from this validation and leave the other 192 uncached.
- 2026-09-02 — Bind new mesh caches to canonical identity, relative source label path/hash, affine, observed IDs, dictionary, full/display algorithms and parameters, and code/schema versions; publish only validated cache directories atomically.
- 2026-09-02 — Preserve the accepted Afterthought cache through legacy provenance validation rather than rewriting it, and use one shared application for both general and compatibility entry points.
- 2026-09-02 — Keep split policy, preprocessing, training, inference, evaluation, public deployment, and Phase 1A completion explicitly deferred.

## Validation

### Passed

- All-record 3D selector audit — 202/202 verified unique IDs are selectable: Extra-18 36, MMRR-21 42, NKI-RS-22 44, NKI-TRT-20 40, OASIS-TRT-20 40; exactly 101 native and 101 MNI152; no invalid/unverified row offered.
- Representative 3D audit — exactly 10 records (one native and one MNI152 per cohort) passed read-only loading, 62-region coverage, finite vertices, valid triangular faces, recorded world bounds, independent affine reconstruction, hemisphere/region controls, three-plane rendering, raw preservation, and cached reload.
- Cache audit — accepted Afterthought cache reused unchanged; nine caches generated atomically; synthetic stale identity rejected; synthetic incomplete cache detected/recovered outside accepted caches; one non-Afterthought repeat generation was byte-identical.
- General application audit — Streamlit selector transition completed with zero exceptions, local health returned HTTP 200/`ok`, generic and compatible launchers passed, and the existing automated suite passed 8/8.
- All-record viewer preservation — before/after bundle hashes matched for raw archives, manifests, accepted QC and lineage CSVs, dictionary, accepted loader/2D logic, and the complete legacy Afterthought cache.

- Proposed CSV schemas — exact expected headers, unique columns, successful parsing, and 0 invented data rows at initialization.
- Phase 1A directory/ignore protections — required directories exist; raw neuroimaging, derived/cache, and Python-cache patterns are ignored.
- Raw inventory — 24 unique rows cover 24 files totaling 7,984,131,445 bytes; hashes reproduced on two complete passes; Harvard Dataverse v2 names/sizes matched with 0 missing, unexpected, duplicate-name, or size-mismatched files.
- Raw Git boundary — 0 raw files tracked and all 24 covered by `.gitignore`.
- Extra-18 archive and extraction — checksum, gzip/tar integrity, 183 safe member paths, 0 link/special entries, and exact archive/disk member correspondence passed.
- Extra-18 extracted inventory — 164 files, 144 NIfTIs, 18 subjects, 72 native NIfTIs, and 72 MNI152 NIfTIs.
- Extra-18 metadata/pairing — all 18 IDs occur in supplied metadata; 18 native and 18 MNI152 canonical pairs; 0 missing/ambiguous pairs or cross-space path mismatches.
- Extra-18 MRI/label QC — 36/36 passed parsing, exact 3D shape matching, affine, orientation, spacing, declared-space, finite-value, MRI content/variation, label-integrality/vocabulary, segmentation nonemptiness, and technical overlap checks.
- Extra-18 label vocabulary — every nonzero anatomical ID occurs in the distributed 62-row cortical DKT block; unknown IDs: 0.
- Exact duplicate analysis — 0 exact compressed-file, decoded MRI, decoded label, or whole-pair voxel duplicates among canonical rows.
- Automated tests — 8/8 passed on each of two runs.
- QC determinism — two complete runs produced byte-identical pair-QC, failure, dictionary, and updated-manifest CSVs.
- Raw preservation — post-QC Extra-18 archive SHA-256 `89e5d9a635fb12227e3c132d33ecb15aeeaeb54a7db02ad29ecfa7085468eb9c` matches the prior inventory.
- MMRR-21 archive/extraction — checksum matched inventory; 211 unique safe regular-file/directory members; 0 unsafe paths, links, special entries, or overwrite risks; extracted disk entries match exactly.
- MMRR-21 inventory — 189 files, 168 NIfTIs, 21 subjects, 84 native and 84 MNI152 NIfTIs, 0 unexpected NIfTIs, 21 native and 21 MNI152 unambiguous canonical candidates.
- MMRR-21 metadata comparison — all 21 subjects match subject-list, subject-source, and scan-information sources; supplied repeat mappings recorded for subjects 1–10 and absent for 11–21.
- MMRR-21 MRI/label QC — 42/42 pairs passed all accepted technical checks; 21 native and 21 MNI152 pairs verified; unknown observed IDs: 0; exact file/voxel/pair duplicates: 0.
- MMRR-21 automated tests/QC determinism — 8/8 tests passed twice; both QC runs produced byte-identical manifest, pair-QC, and failure CSVs.
- Existing-QC preservation — `src/brain_segmentation/qc.py`, the 62-row dictionary, and accepted Extra-18 CSV hashes remained unchanged.
- MMRR-21 raw preservation — post-QC archive SHA-256 `73b27f5ccce27a47e6cf03b9a1adc64b191d677009340feb531793e0fa83eeb1` matches inventory.

- MMRR-21 lineage resolution — 42 scan records map to 21 unique participant groups; the 42-session demographics table confirms one external counterpart session for every included acquisition, including subjects 11–21.
- MMRR-21 label-issue review — six metadata entries across five subjects reconciled; 0 exclusions, 6 annotation-only actions, and none of IDs 1032, 1033, 2032, or 2033 observed in canonical voxels.
- Metadata-review determinism — two runs produced byte-identical lineage, label-issue, and augmented-manifest CSVs while accepted QC artifacts and the raw archive retained their established hashes.
- NKI-RS-22 archive/inventory — checksum matched inventory; 221 safe members exactly match disk; 198 files, 176 NIfTIs, 22 subjects, and 0 unexpected NIfTIs.
- NKI-RS-22 MRI/label QC — 44/44 pairs verified (22 native, 22 MNI152); 0 failed or blocked checks, unknown observed IDs, or duplicates.
- NKI-RS-22 lineage — 22 participant groups confirmed; 21 acquisition sessions resolved and one preserved as ambiguous; no repeat acquisition is documented among included rows.
- NKI-RS-22 label review — 18 metadata entries across seven subjects; 7 annotation-only, 11 not applicable to canonical DKT31, 0 exclusions.
- NKI-RS-22 repeated validation — automated tests passed 8/8 twice; QC and metadata outputs were byte-identical across two runs; prior Extra-18/MMRR-21 artifacts remained unchanged.
- NKI-TRT-20 archive/inventory — checksum matched inventory; 201 safe members match disk; 180 files, 160 NIfTIs, 20 subjects, and 0 unexpected NIfTIs.
- NKI-TRT-20 MRI/label QC — 40/40 pairs verified (20 native, 20 MNI152); 0 failures, blocks, unknown observed IDs, or duplicates.
- NKI-TRT-20 lineage/overlap — 20 participant and repeat groups confirmed; two exact NKI-RS participant overlaps and 15 wider-NKI metadata matches recorded; sessions and temporal roles remain unresolved.
- NKI-TRT-20 label review — 397 issue-ID records across eight subjects; 12 annotation-only, 385 not applicable to canonical DKT31, 0 exclusions.
- NKI-TRT repeated validation — tests passed 8/8 twice; QC and metadata outputs were byte-identical; all previously accepted artifacts and archive hashes remained unchanged.
- OASIS-TRT-20 archive/inventory — checksum matched inventory; 201 safe members match disk; 180 files, 160 NIfTIs, 20 subjects, and 0 unexpected NIfTIs.
- OASIS-TRT-20 MRI/label QC — 40/40 pairs verified (20 native, 20 MNI152); 0 failures, blocks, unknown IDs, or duplicates.
- OASIS-TRT-20 lineage/overlap — 20 participant and repeat groups, 18 tests, two retests, and 20 counterpart sessions resolved; all 20 confirmed in OASIS-1 reliability data, with no other Mindboggle overlap.
- OASIS-TRT-20 label review — nine annotation-only issue-ID records across eight subjects; 0 exclusions.
- OASIS repeated validation — tests passed 8/8 twice; QC/metadata outputs were byte-identical; all prior artifacts, archive hashes, and accepted NKI shared groups remained unchanged.
- Global manifest counts/status — 101 subject records and 202 verified canonical rows, exactly 101 native and 101 MNI152; every subject has one verified pair in each space and no ambiguous pair remains.
- Global grouping audit — 99 unique participant groups derived from actual records; two documented NKI cross-cohort groups and 61 repeat/counterpart grouping constraints are preserved consistently across spaces.
- Global uniqueness/vocabulary audit — 0 duplicate scan IDs, pair IDs, paths, exact files, or decoded voxel products; 0 missing paths, space mismatches, group conflicts, exclusions, or unknown observed label IDs.
- Global traceability — all 202 rows trace to one accepted cohort inventory row, QC row, source archive, applicable lineage evidence, and applicable label-review evidence.
- Global determinism/preservation — two generation passes produced nine byte-identical outputs; all five raw archive checksums and 27 established accepted cohort/code/dictionary artifact hashes remained unchanged.
- Extra-18 visualization pair validation — 23/23 real-pair checks passed: file existence/parsing, 3D shape, affine at existing tolerances, spacing, LAS orientation, finite/nonconstant MRI, integer/nonempty labels, dictionary vocabulary, manifest agreement, and same-subject native-space identity.
- Extra-18 visualization rendering — axial, coronal, sagittal, and combined views rendered; three slice controls, opacity, MRI-only/label-only/overlay modes, anatomical labels, transparent background, deterministic label colors, and label ID/region display all passed.
- Extra-18 visualization slice rule — nonzero-extent center deterministically produced sagittal `89`, coronal `121`, and axial `159`.
- Extra-18 visualization regression/determinism — existing QC tests passed 8/8 once; two final rendering runs produced byte-identical four screenshots and validation JSON.
- Extra-18 visualization preservation — selected NIfTI hashes were identical before/after; 11 global accepted artifacts plus 25 accepted cohort artifacts and all five raw archives retained established hashes.
- Manifest viewer catalog/selection — 202/202 verified pairs and canonical IDs resolve uniquely; supported cohort totals are Extra-18 36, MMRR-21 42, NKI-RS-22 44, NKI-TRT-20 40, and OASIS-TRT-20 40.
- Manifest viewer smoke validation — exactly 10/10 selected pairs passed loading, essential scientific checks, three-plane rendering, controls, color/transparency, label lookup, and before/after NIfTI hashing; 0 failed and 0 smoke screenshots were created.
- Manifest viewer orientation/error handling — all six observed orientation codes produced valid anatomical-axis mappings; an invalid canonical ID returned a clear error and exit code 2 without an unhandled crash.
- Manifest viewer regression/preservation — existing QC tests passed 8/8 once; all 47 accepted preservation-baseline files and the 20 selected source NIfTIs remained unchanged.
- Focused sagittal transformation audit — slice 89 uses voxel axis 0, identical `transpose(1,0)`, no rotation/flip, matching origin/extents/aspect/interpolation, and exact expected MRI/label display arrays.
- Focused source-support audit — full-volume MRI/label nonzero counts are 1,157,182/434,509 and slice-89 counts are 6,040/1,720; both have 0 label voxels on zero MRI (0.0%).
- Focused cause assessment — label-supported slice-89 MRI values span 49–201 on the unchanged 0–281 window, and original label-component counts peak at 64 on slice 89 versus 16/24/27/15 nearby; source-pair morphology, not display logic or faint-tissue windowing, explains the appearance.
- Focused usability acceptance — all required selectors, pair updates, plane sliders, opacity isolation, display modes, label lookup, invalid-ID recovery, colors/transparency, and manual-reference notice checks passed for the three required records.
- Focused visual preservation — no dependency or accepted viewer-code change was made; selected NIfTI hashes matched before and after and the accepted artifact baseline remained unchanged.
- Split-policy evidence audit — the accepted subject, scan-space, and participant-group inputs parse as 101, 202, and 99 rows; 97 groups have one included record, two shared NKI groups have two, and 61 groups carry repeat/counterpart constraints.
- Split-policy scope control — the `splits/` directory remains empty and no participant, subject, or canonical pair was assigned.
- Afterthought-1 3D mesh audit — 62/62 observed foreground IDs, 31 per hemisphere, and all 434,509 foreground label voxels map to valid finite triangular surfaces; unknown IDs and background meshes are 0.
- Professor-demo interaction audit — Plotly orbit/scroll zoom, original-ID/name hover, hemisphere and region filtering, 3D/2D opacity, all anatomical slice sliders, and MRI-only/label-only/overlay modes passed.
- Streamlit and launcher audit — focused AppTest completed with 0 exceptions, the local server returned HTTP 200 / `ok`, and the Windows one-click launcher validation returned code 0.
- Professor-demo determinism/regression — two complete generations produced 255 byte-identical artifacts; existing automated tests passed 8/8.
- Professor-demo preservation — selected raw NIfTI hashes and accepted loader, 2D viewer, manifests, dictionaries, QC, lineage, grouping, and archive artifacts remained unchanged; split files and other-record mesh directories remain 0.

### Failed

- None for the five scoped cohort checkpoints, global consolidation checkpoint, Extra-18 visualization pre-MVP, manifest-driven 2D viewer, focused visual acceptance, split-policy evidence review, Afterthought-1 3D demo, or all-record on-demand 3D viewer technical validation.

### Skipped

- Pre-generation of the remaining 192 verified 3D caches, exhaustive 202-record rendering, public deployment, and target-classroom device testing were intentionally skipped.

- Extra-18 full-head T1 and `manual+aseg` auxiliary files.
- Exhaustive focused visual review of the remaining 199 verified records, extensive synthetic loader tests, global split assignment, preprocessing, training, inference, quantitative model evaluation, and 3D surface reconstruction.
- Deterministic split allocation and leakage audit were intentionally skipped pending human policy approval.
- Mesh generation for the other 201 canonical rows, 3D MRI volume rendering, preprocessing, training, inference, quantitative evaluation, and clinical validation were intentionally skipped.

### Unverified

- Professor usability and performance on the target presentation computer, browser, display, and GPU for the all-record on-demand viewer.

- Harvard Dataverse v2 versus OSF/project v3 equivalence.
- Exact source-directory fidelity.
- Cross-release acquisition lineage beyond reviewed local MMRR, NKI, and OASIS-1 evidence.
- MMRR-21 temporal scan/rescan role because original session identifiers were randomized.
- Exact distributed product intended by the March 2019 MMRR label-issue notice; cited IDs were not observed in current canonical data.
- NKI-RS-22-16 exact acquisition session (`MR_3927656_3303` versus `MR_3927656_3268`), external NKI repeat/overlap status, and exact product intended by the March 2019 NKI label notice.
- NKI-TRT-20 included/counterpart sessions and scan/rescan roles; acquisition relationship for the two shared NKI-RS participants; additional external-NKI identities beyond exact supplied source matches.
- OASIS-2, OASIS-3, and other external OASIS derivative overlap beyond the confirmed OASIS-1 reliability identity.
- Independent MNI152 template provenance beyond distributed filenames and observed within-pair geometry.
- Scientific and clinical validity.
- Human selector usability across different monitor, DPI, and Matplotlib/Tk backend configurations.
- Focused visual alignment of the other 199 canonical records; this milestone intentionally reviewed exactly three records.
- Whether the proposed 70/15/16 ratio, cohort target matrix, seed `20260831`, and MNI152-first modeling recommendation match the final thesis design.
- Professor usability and presentation quality on the target classroom display, GPU, and browser; technical headless/local-server validation does not substitute for that review.

### Blocked

- Package/component licensing reconciliation requires human review.
- Phase transition, split-policy approval, and licensing decisions require human review; dataset splitting remains deferred.
- Phase 1A completion is not claimed; professor feedback and subsequent explicit user authorization are required before selecting another milestone.

## Next milestone

- Launch `launch_mindboggle101_3d_viewer.cmd` for a bounded professor walkthrough using the cached default and one cross-cohort/native-or-MNI selection, then record usability and scientific-display feedback. Do not generate splits, revisit split approval, or claim Phase 1A completion during that review.
