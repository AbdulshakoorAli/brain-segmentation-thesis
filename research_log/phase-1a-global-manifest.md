# Research log: Phase 1A global manifest consolidation

- Date: 2026-08-27
- Skill: repository-local `brain-segmentation-research`.
- Scope: consolidate five accepted cohort manifests/QC/lineage/issue artifacts; reconcile global groups; audit provenance and overlap.
- Boundaries: no raw processing, combined split, loader, training, or visualization.

## Result

- 101 subject/acquisition rows and 202 verified scan-space rows (101 native, 101 MNI152).
- 99 participant groups derived from actual rows; two shared NKI groups preserved.
- 61 repeat/counterpart grouping constraints represented.
- No duplicate IDs, paths, exact file/voxel content, space mismatch, missing pair, group conflict, exclusion, or unknown observed label ID.
- Every scan row traces to inventory, accepted QC, source archive, lineage evidence, and label-review evidence.
- External provenance uncertainties remain explicit and do not alter accepted technical QC.

## Validation

- Consolidation generator: `scripts/build_mindboggle101_global_manifest.py`.
- Audit: 26 passed, 0 failed, 4 unverified, 1 blocked provenance item.
- Determinism is established by running the generator twice and comparing byte-level hashes of all eight generated artifacts.
- Accepted cohort artifacts, dictionary, shared QC implementation, and raw archives are hash-checked externally after generation.

## Outcome

The consolidated global manifest passes this scoped Phase 1A checkpoint and is ready for a minimal read-only loader milestone after human approval. Splits remain deferred.
