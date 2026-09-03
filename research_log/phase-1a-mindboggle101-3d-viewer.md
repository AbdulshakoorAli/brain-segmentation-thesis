# Research log: manifest-driven on-demand Mindboggle-101 3D viewer

- Date: 2026-09-02
- Skill: repository-local `brain-segmentation-research`
- Initiating request: extend the accepted single-record Streamlit demo into one manifest-driven, on-demand application for all 202 verified Mindboggle-101 MRI/manual-DKT31 pairs.
- Intended deliverables: verified selectors, atomic provenance-bound mesh caching, exactly ten representative real caches, cache failure scenarios, deterministic generation evidence, shared app/launcher, screenshots, report, and project-state update.
- Boundaries: no pre-generation of all records, split policy, split files, preprocessing, training, inference, evaluation, clinical claims, public deployment, raw-data writes, or Phase 1A completion claim.

## Implementation record

- Reused `loading.py`, `visualization.py`, deterministic label colors, and the accepted full/display marching-cubes implementation.
- Added a versioned cache layer keyed by a safe SHA-256-derived directory name. New caches are bound to source/dictionary hashes, affine, observed IDs, algorithms/parameters, schema/code versions, and mesh levels.
- Added atomic temporary-directory generation and post-generation geometry validation. Existing valid caches are returned unchanged; known-invalid synthetic caches can be quarantined rather than silently deleted.
- Added the shared Streamlit implementation and general entry point. The old Afterthought entry point and launcher now redirect compatibly to the general viewer.
- Added no dependency.

## Validation result

- 202/202 verified canonical IDs resolved uniquely; no unverified or excluded row was offered. Counts were 36/42/44/40/40 by cohort and 101/101 by native/MNI152 space.
- Reused the accepted Afterthought native cache and generated nine new representative caches. The ten examples covered LAS, RPS, LIA, and ASL.
- All ten pairs passed the accepted read-only loader. Each had 62 observed foreground regions; all 62 were meshed with finite vertices, valid faces, recorded world bounds, and independently confirmed single affine application.
- Generation/validation took 28.746–63.685 seconds for new caches; provenance/geometry cached reload took 0.578–0.824 seconds.
- Synthetic stale metadata was rejected. A synthetic incomplete cache was detected and quarantined without accepted-cache damage. Repeated non-Afterthought generation was byte-identical.
- Streamlit AppTest completed the required selector transition with zero exceptions; the local health endpoint returned HTTP 200/`ok`; both generic and compatibility launcher validations passed.
- Existing automated tests passed 8/8. Eight focused screenshots were created.
- Raw archives, manifests, accepted QC/lineage artifacts, dictionary, accepted loader/2D logic, and all legacy Afterthought cache files retained identical before/after bundle hashes.

## Accounting

- Passed: selector, source validation, geometry, affine, region coverage, controls, caching, invalidation/recovery, determinism, health, launcher, regression, screenshots, and preservation checks.
- Failed: none.
- Skipped: the other 192 mesh caches, exhaustive device/browser testing, splitting, preprocessing, and all model work.
- Unverified: professor experience on the target classroom system and unresolved dataset licensing/provenance questions.
- Blocked: Phase transition and licensing reconciliation remain human decisions.

The scoped manifest-driven, on-demand 3D viewer passes technical validation. The manual labels remain references, not predictions. Phase 1A is not claimed complete.

