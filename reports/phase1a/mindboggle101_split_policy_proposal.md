# Mindboggle-101 participant-grouped split policy proposal

## Status

This document is a **scientific-design proposal awaiting human approval**. It does not assign any participant, subject record, or scan-space record to train, validation, or test. The `splits/` directory remains empty.

## Evidence reviewed

- `data/derived/manifests/mindboggle101_subject_manifest.csv`
- `data/derived/manifests/mindboggle101_scan_manifest.csv`
- `data/derived/metadata/mindboggle101_participant_groups.csv`
- accepted cohort lineage and cross-cohort overlap reviews
- the Phase 1A leakage-safe split guidance

The accepted inputs contain 101 included subject/acquisition records, 202 verified scan-space rows, and 99 participant groups. Ninety-seven groups contain one included subject record and two groups contain two records. The two multi-record groups are the confirmed cross-cohort NKI relationships:

- `NKI-Rockland-1427581`: NKI-RS-22-3 and NKI-TRT-20-5;
- `NKI-Rockland-3808535`: NKI-RS-22-14 and NKI-TRT-20-14.

The cohort subject-record counts are Extra-18 18, MMRR-21 21, NKI-RS-22 22, NKI-TRT-20 20, and OASIS-TRT-20 20. Sixty-one participant-group rows carry documented repeat/counterpart constraints for MMRR, NKI-TRT, or OASIS. Counterpart acquisitions that are not included in Mindboggle-101 cannot be assigned now, but their identifiers must remain reserved as same-split constraints in any later combined dataset.

## Recommended policy

### Assignment unit

Assign only by `participant_group_id`. Each participant group is indivisible. All included subject/acquisition records in a group, both native and MNI152 rows for every record, and any later documented counterpart must inherit the same split.

Do not use `scan_id`, `canonical_pair_id`, cohort-local subject numbering, filename, coordinate space, or unresolved temporal role as the assignment unit.

### Target sizes

Use the Phase 1A initial target of 70 train, 15 validation, and 16 test **subject/acquisition records**. Participant grouping has higher priority than exact totals, although the observed group-size distribution makes the exact overall target potentially feasible.

The proposed secondary cohort targets are:

| Cohort | Train | Validation | Test | Total |
|---|---:|---:|---:|---:|
| Extra-18 | 13 | 3 | 2 | 18 |
| MMRR-21 | 15 | 3 | 3 | 21 |
| NKI-RS-22 | 15 | 3 | 4 | 22 |
| NKI-TRT-20 | 14 | 3 | 3 | 20 |
| OASIS-TRT-20 | 13 | 3 | 4 | 20 |
| **Total** | **70** | **15** | **16** | **101** |

These are balancing targets, not permission to split either shared NKI group. If exact cohort targets conflict with participant integrity, participant integrity wins and the deviation must be reported.

### Determinism

Recommended seed: integer `20260831`.

The later implementation should use a version-independent deterministic rank derived from SHA-256 of `seed|participant_group_id`, not the iteration order of a CSV or an unrecorded pseudo-random generator state. A deterministic grouped allocator should apply this objective hierarchy:

1. zero participant-group overlap across splits;
2. keep all native/MNI152 and cross-cohort records in the group together;
3. reach 70/15/16 subject-record totals if feasible;
4. minimize absolute deviation from the cohort targets above;
5. resolve equal-scoring assignments by the stable SHA-256 group rank.

The algorithm, seed, input hashes, objective values, and software version must be recorded. Running it twice with identical inputs must produce byte-identical outputs.

### Coordinate-space rule

The split assignment should cover both native and MNI152 manifest rows, but the two products from one acquisition must not be treated as independent participants. A later modeling configuration should select one coordinate-space policy explicitly.

For the first minimal segmentation experiment, MNI152-only is the recommended candidate because all accepted MNI152 pairs share common geometry. That recommendation is **not approved by this proposal** and must be reviewed separately for scientific suitability. If both representations are ever used, they must remain in the same split and their dependency must be disclosed.

### Test-set rule

After approval and deterministic generation, freeze the test participant groups. Test data must not influence preprocessing choices, architecture selection, threshold selection, early stopping, or hyperparameter tuning. Validation may support those development decisions; test evaluation should occur only after the analysis plan is fixed.

### External-overlap rule

The unresolved NKI acquisition/session mappings, OASIS-2/OASIS-3 row-level overlap, MMRR temporal roles, and wider external counterpart relationships are not internal Mindboggle technical-QC failures. They do prohibit treating future external OASIS, NKI, or MMRR records as independent until identifiers are reconciled. Any matching or documented counterpart must inherit the existing Mindboggle participant group's split or be excluded from the combined benchmark.

### Label and exclusion rule

Use all 101 accepted subject records: current technical QC reports 0 exclusions and 0 unknown observed label IDs. Historical label notices remain annotations. Do not silently exclude, relabel, or remap records during splitting.

## Alternatives requiring an explicit design change

- **Cohort-held-out test:** stronger domain-shift evaluation, but it changes the scientific question and would not preserve the proposed proportional cohort balance.
- **Cross-validation:** useful for uncertainty with 99 groups, but more expensive and incompatible with a single initially frozen test set unless nested deliberately.
- **Different ratios or seed:** acceptable only when selected before examining model results and recorded with rationale.
- **Native-only first experiment:** preserves distributed native geometry but requires an explicit preprocessing/patching design because shapes and orientations vary.

## Required later split artifacts

Only after approval, create a separate deterministic split-generation milestone producing at least:

- `splits/mindboggle101_subject_splits.csv`;
- `splits/mindboggle101_scan_space_splits.csv`;
- `data/derived/qc/mindboggle101_split_audit.csv`;
- `data/derived/qc/mindboggle101_split_failures.csv`;
- a machine-readable split configuration containing seed, algorithm, targets, input hashes, and policy version;
- a split report, research log, and `PROJECT_STATE.md` update.

The audit must prove 101/101 subject records and 202/202 scan-space rows are assigned exactly once, both spaces agree, shared NKI groups remain intact, no participant group overlaps, all cohort/total deviations are explicit, and repeated generation is byte-identical.

## Human approval requested

Before split generation, approve or revise these four choices:

1. assignment by the 99 accepted `participant_group_id` values;
2. 70/15/16 subject-record targets with the proposed cohort-balance matrix;
3. deterministic seed `20260831` and SHA-256-based tie-breaking;
4. freezing the test set and postponing the modeling coordinate-space choice, with MNI152-only as the initial recommendation.

Licensing reconciliation, Dataverse v2 versus OSF v3 equivalence, NKI acquisition uncertainty, OASIS external overlap, and historical label-notice scope remain unresolved and unchanged.
