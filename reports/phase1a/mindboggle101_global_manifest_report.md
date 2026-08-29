# Mindboggle-101 Global Manifest Consolidation Report

## Checkpoint decision

The consolidated Mindboggle-101 manifest passes this scoped Phase 1A checkpoint. It contains 101 subject/acquisition records and 202 verified canonical scan-space pairs: 101 native and 101 MNI152. The derived global participant-group count is 99, including two confirmed shared NKI groups.

No split, loader, training code, visualization, raw-data modification, or QC-rule change was performed.

## Schema reconciliation and traceability

All five inventory and QC schemas were inspected. Equivalent identity, pairing, geometry, validation, lineage, issue, and evidence columns were mapped explicitly. Cohort-specific source fields remain unchanged in their accepted artifacts and are linked through `inventory_evidence`, `qc_evidence`, `lineage_artifact`, `lineage_evidence`, and `label_issue_evidence` rather than silently discarded.

Every global row traces to exactly one cohort inventory row, one accepted QC row, its source archive, applicable lineage evidence, and an applicable label-review record or no-entry source notice.

## Counts and grouping

- Subject/acquisition records: 101.
- Canonical scan-space records: 202.
- Native/MNI152: 101/101.
- Verified rows: 202; exclusions: 0.
- Unique participant groups: 99.
- Cross-cohort shared groups: 2.
- Repeat/counterpart-constrained groups: 61 (21 MMRR, 20 NKI-TRT, 20 OASIS).

The actual records preserve `NKI-Rockland-1427581` for NKI-RS-22-3/NKI-TRT-20-5 and `NKI-Rockland-3808535` for NKI-RS-22-14/NKI-TRT-20-14. Both coordinate spaces for every included subject share one participant group and future split constraint.

## Global uniqueness and label audit

- Duplicate scan IDs: 0.
- Duplicate canonical pair IDs: 0.
- Duplicate MRI/label paths: 0.
- Missing MRI/label paths: 0.
- Native/MNI space mismatches: 0.
- Conflicting global group assignments: 0.
- Unexplained source-identity conflicts: 0; documented NKI aliases are reconciled by evidence.
- Exact compressed-file duplicates: 0.
- Exact decoded MRI/label voxel duplicates: 0.
- Unknown observed label IDs: 0; the accepted 62-row DKT dictionary is unchanged.

## Unresolved provenance and combination constraints

- NKI-RS-22-16 retains candidate sessions `MR_3927656_3303` and `MR_3927656_3268`.
- NKI-TRT included/counterpart sessions and temporal roles remain unresolved.
- Exact acquisition relationship for the two shared NKI participants remains unresolved.
- OASIS-2/OASIS-3 row-level overlap remains unresolved.
- Exact historical label-notice product scope remains unresolved.
- Licensing and Harvard Dataverse v2 versus OSF/project v3 equivalence remain unresolved.

These are external provenance/combination constraints, not failures of internal pair QC.

## Final accounting

### Passed

- 26 global consolidation/audit checks, including all acceptance-critical count, status, grouping, uniqueness, label-vocabulary, and traceability checks.

### Failed

- None.

### Skipped

- Train/validation/test splits, loader implementation, training, and visualization.

### Unverified

- 4 audit items covering external overlap, historical product scope, version equivalence, and the NKI session conflict.

### Blocked

- 1 audit item: licensing reconciliation requires human review.

## Readiness and next task

The global manifest is ready for a minimal data-loader milestone because every canonical pair is verified, traceable, group-consistent, and label-dictionary compliant. Split creation remains premature.

Exact next recommended task: obtain human approval for this global manifest and its unresolved provenance constraints, then implement only a minimal read-only loader contract with representative tests across all five cohorts; continue to defer splits until the loader and final split-policy review are approved.
