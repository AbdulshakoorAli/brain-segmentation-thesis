# Mindboggle-101 Deterministic Split Report

Date: 2026-09-20

## Scope

This Phase 1B milestone generated deterministic train/validation/test assignments only. It did not modify raw data, generate preprocessing outputs, install training dependencies, implement a model, or begin training.

## Approved policy

- Training space: MNI152-first.
- Classes: 63 total, with background class 0 and the 62 documented DKT foreground labels mapped reversibly.
- Grouping key: `participant_group_id`.
- Seed: `20260831`.
- Tie-breaking: SHA-256 over stable canonical fields.
- Subject-record targets: train 70, validation 15, test 16.
- Test set: frozen under split version `phase1b-1.0-seed20260831-participant_group_id-approved-20260920`.

## Achieved allocation

Subject-record counts: {"test": 16, "train": 70, "validation": 15}

Participant-group counts: {"test": 16, "train": 69, "validation": 14}

MNI152 training-pair counts: {"test": 16, "train": 70, "validation": 15}

Native traceability-pair counts: {"test": 16, "train": 70, "validation": 15}

Cohort-by-split matrix:

```json
{
  "test": {
    "Extra-18": 3,
    "MMRR-21": 3,
    "NKI-RS-22": 4,
    "NKI-TRT-20": 3,
    "OASIS-TRT-20": 3
  },
  "train": {
    "Extra-18": 12,
    "MMRR-21": 15,
    "NKI-RS-22": 15,
    "NKI-TRT-20": 14,
    "OASIS-TRT-20": 14
  },
  "validation": {
    "Extra-18": 3,
    "MMRR-21": 3,
    "NKI-RS-22": 3,
    "NKI-TRT-20": 3,
    "OASIS-TRT-20": 3
  }
}
```

Shared NKI groups:

```json
{
  "NKI-Rockland-1427581": [
    "MB101-SUBJECT:NKI-RS-22:NKI-RS-22-3",
    "MB101-SUBJECT:NKI-TRT-20:NKI-TRT-20-5"
  ],
  "NKI-Rockland-3808535": [
    "MB101-SUBJECT:NKI-RS-22:NKI-RS-22-14",
    "MB101-SUBJECT:NKI-TRT-20:NKI-TRT-20-14"
  ]
}
```

## Validation

Audit checks passed: 22

Audit checks failed: 0

Failure details:

```json
[]
```

## Unresolved cautions

These remain documented but are not internal split failures: licensing reconciliation, Dataverse v2 versus OSF v3 equivalence, NKI session and acquisition uncertainties, exact acquisition relationship for the shared NKI participants, OASIS-2/OASIS-3 row-level overlap, historical label-notice product scope.

## Next recommended task

Review the frozen split artifacts and, if accepted, authorize the next smallest milestone: read-only planning for preprocessing implementation using the MNI152 training-space split.
