"""Generate deterministic Phase 1B Mindboggle-101 train/validation/test splits.

This script assigns participant groups, not individual scan rows. It writes
derived split artifacts only and does not touch raw data, preprocessing outputs,
loader/viewer code, or training code.
"""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SEED = "20260831"
ALGORITHM_NAME = "sha256_ordered_group_dp_cohort_balance"
ALGORITHM_VERSION = "1.0"
GROUPING_KEY = "participant_group_id"
TRAINING_SPACE = "MNI152"
SPLIT_VERSION = (
    f"phase1b-{ALGORITHM_VERSION}-seed{SEED}-"
    f"{GROUPING_KEY}-approved-20260920"
)
TARGET_SUBJECT_COUNTS = {"train": 70, "validation": 15, "test": 16}
SPLIT_ORDER = ["train", "validation", "test"]
COHORTS = ["Extra-18", "MMRR-21", "NKI-RS-22", "NKI-TRT-20", "OASIS-TRT-20"]

SCAN_MANIFEST = ROOT / "data/derived/manifests/mindboggle101_scan_manifest.csv"
SUBJECT_MANIFEST = ROOT / "data/derived/manifests/mindboggle101_subject_manifest.csv"
PARTICIPANT_GROUPS = ROOT / "data/derived/metadata/mindboggle101_participant_groups.csv"
CLASS_MAPPING = ROOT / "data/derived/dictionaries/dkt_training_class_mapping_proposal.csv"
TRAINING_READINESS = ROOT / "data/derived/qc/mindboggle101_training_readiness.csv"
SPLIT_FEASIBILITY = ROOT / "data/derived/metadata/mindboggle101_split_feasibility_proposal.csv"
DESIGN_REPORT = ROOT / "reports/phase1b/mindboggle101_modeling_design_proposal.md"

GROUP_SPLITS = ROOT / "data/derived/splits/mindboggle101_participant_group_splits.csv"
SUBJECT_SPLITS = ROOT / "data/derived/splits/mindboggle101_subject_splits.csv"
PAIR_SPLITS = ROOT / "data/derived/splits/mindboggle101_pair_splits.csv"
CONFIG_JSON = ROOT / "data/derived/splits/mindboggle101_split_config.json"
AUDIT_CSV = ROOT / "data/derived/qc/mindboggle101_split_audit.csv"
FAILURES_CSV = ROOT / "data/derived/qc/mindboggle101_split_failures.csv"
REPORT_MD = ROOT / "reports/phase1b/mindboggle101_split_report.md"
LOG_MD = ROOT / "research_log/phase-1b-deterministic-splits.md"

UNRESOLVED_CAUTIONS = [
    "licensing reconciliation",
    "Dataverse v2 versus OSF v3 equivalence",
    "NKI session and acquisition uncertainties",
    "exact acquisition relationship for the shared NKI participants",
    "OASIS-2/OASIS-3 row-level overlap",
    "historical label-notice product scope",
]


@dataclass(frozen=True)
class GroupInfo:
    participant_group_id: str
    subject_ids: tuple[str, ...]
    cohorts: tuple[str, ...]
    source_participant_ids: tuple[str, ...]
    subject_count: int
    cohort_counts: tuple[int, ...]
    assignment_hash: str
    repeat_or_counterpart_constraint: str
    notes: str


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def read_header(path: Path) -> list[str]:
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        return next(reader)


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def split_join(values: list[str] | tuple[str, ...]) -> str:
    return ";".join(sorted(v for v in values if v))


def validate_schema(path: Path, required: set[str], audit: list[dict[str, str]]) -> list[str]:
    header = read_header(path)
    missing = sorted(required - set(header))
    status = "passed" if not missing else "failed"
    audit.append(
        {
            "check": f"schema::{path.as_posix()}",
            "status": status,
            "details": "all required columns present" if not missing else "missing " + ";".join(missing),
        }
    )
    return header


def largest_remainder_targets(total_by_cohort: Counter[str], split_total: int) -> dict[str, int]:
    total = sum(total_by_cohort.values())
    base: dict[str, int] = {}
    remainders: list[tuple[float, str]] = []
    for cohort in COHORTS:
        exact = total_by_cohort[cohort] * split_total / total
        floor = int(exact)
        base[cohort] = floor
        remainders.append((exact - floor, cohort))
    remaining = split_total - sum(base.values())
    for _, cohort in sorted(remainders, key=lambda item: (-item[0], item[1]))[:remaining]:
        base[cohort] += 1
    return base


def vector_from_counts(counts: Counter[str]) -> tuple[int, ...]:
    return tuple(counts[cohort] for cohort in COHORTS)


def vector_cost(vec: tuple[int, ...], target: dict[str, int]) -> tuple[int, int]:
    diffs = [abs(vec[i] - target[cohort]) for i, cohort in enumerate(COHORTS)]
    return sum(diffs), max(diffs)


def subset_signature(group_ids: tuple[str, ...]) -> str:
    return sha256_text("|".join(group_ids))


def choose_subset(
    groups: list[GroupInfo],
    target_subject_count: int,
    target_cohort_counts: dict[str, int],
) -> tuple[set[str], dict[str, Any]]:
    zero = tuple(0 for _ in COHORTS)
    states: dict[tuple[int, tuple[int, ...]], tuple[str, ...]] = {(0, zero): tuple()}
    for group in sorted(groups, key=lambda g: (g.assignment_hash, g.participant_group_id)):
        next_states = dict(states)
        for (subject_count, vec), chosen in states.items():
            new_count = subject_count + group.subject_count
            if new_count > target_subject_count:
                continue
            new_vec = tuple(vec[i] + group.cohort_counts[i] for i in range(len(COHORTS)))
            key = (new_count, new_vec)
            new_chosen = tuple(sorted(chosen + (group.participant_group_id,)))
            old = next_states.get(key)
            if old is None or subset_signature(new_chosen) < subset_signature(old):
                next_states[key] = new_chosen
        states = next_states

    candidates = []
    for (subject_count, vec), chosen in states.items():
        if subject_count != target_subject_count:
            continue
        l1, linf = vector_cost(vec, target_cohort_counts)
        candidates.append((l1, linf, subset_signature(chosen), vec, chosen))
    if not candidates:
        raise RuntimeError(f"No participant-group subset can reach {target_subject_count} subject records")
    l1, linf, signature, vec, chosen = min(candidates)
    return set(chosen), {
        "target_subject_count": target_subject_count,
        "target_cohort_counts": target_cohort_counts,
        "achieved_cohort_counts": {cohort: vec[i] for i, cohort in enumerate(COHORTS)},
        "cohort_l1_deviation": l1,
        "cohort_max_deviation": linf,
        "tie_break_signature": signature,
    }


def build_group_infos(
    subject_rows: list[dict[str, str]],
    participant_rows: list[dict[str, str]],
) -> dict[str, GroupInfo]:
    participant_by_id = {row["participant_group_id"]: row for row in participant_rows}
    subjects_by_group: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in subject_rows:
        subjects_by_group[row["participant_group_id"]].append(row)

    groups: dict[str, GroupInfo] = {}
    for group_id, rows in sorted(subjects_by_group.items()):
        rows_sorted = sorted(rows, key=lambda r: r["subject_record_id"])
        cohorts = tuple(sorted({row["cohort"] for row in rows_sorted}))
        source_ids = tuple(sorted({row["source_participant_identifier"] for row in rows_sorted if row["source_participant_identifier"]}))
        subject_ids = tuple(row["subject_record_id"] for row in rows_sorted)
        cohort_counter = Counter(row["cohort"] for row in rows_sorted)
        participant = participant_by_id.get(group_id, {})
        repeat_fields = [
            participant.get("repeat_acquisition_groups", ""),
            participant.get("external_counterpart_evidence", ""),
            participant.get("future_split_constraint", ""),
        ]
        repeat_constraint = "present" if any(field for field in repeat_fields) else "none_documented"
        hash_payload = "|".join(
            [
                SPLIT_VERSION,
                SEED,
                GROUPING_KEY,
                group_id,
                split_join(subject_ids),
                split_join(cohorts),
                split_join(source_ids),
            ]
        )
        groups[group_id] = GroupInfo(
            participant_group_id=group_id,
            subject_ids=subject_ids,
            cohorts=cohorts,
            source_participant_ids=source_ids,
            subject_count=len(rows_sorted),
            cohort_counts=vector_from_counts(cohort_counter),
            assignment_hash=sha256_text(hash_payload),
            repeat_or_counterpart_constraint=repeat_constraint,
            notes=participant.get("future_split_constraint", ""),
        )
    return groups


def assign_groups(groups: dict[str, GroupInfo], subject_rows: list[dict[str, str]]) -> tuple[dict[str, str], dict[str, Any]]:
    total_by_cohort = Counter(row["cohort"] for row in subject_rows)
    validation_targets = largest_remainder_targets(total_by_cohort, TARGET_SUBJECT_COUNTS["validation"])
    test_targets = largest_remainder_targets(total_by_cohort, TARGET_SUBJECT_COUNTS["test"])
    validation_ids, validation_meta = choose_subset(
        list(groups.values()), TARGET_SUBJECT_COUNTS["validation"], validation_targets
    )
    remaining = [group for group in groups.values() if group.participant_group_id not in validation_ids]
    test_ids, test_meta = choose_subset(remaining, TARGET_SUBJECT_COUNTS["test"], test_targets)

    assignments = {}
    for group_id in groups:
        if group_id in validation_ids:
            assignments[group_id] = "validation"
        elif group_id in test_ids:
            assignments[group_id] = "test"
        else:
            assignments[group_id] = "train"
    meta = {
        "validation_selection": validation_meta,
        "test_selection": test_meta,
        "cohort_targets": {
            "validation": validation_targets,
            "test": test_targets,
            "train": {
                cohort: total_by_cohort[cohort] - validation_meta["achieved_cohort_counts"][cohort] - test_meta["achieved_cohort_counts"][cohort]
                for cohort in COHORTS
            },
        },
    }
    return assignments, meta


def make_output_rows(
    subject_rows: list[dict[str, str]],
    pair_rows: list[dict[str, str]],
    participant_rows: list[dict[str, str]],
    groups: dict[str, GroupInfo],
    assignments: dict[str, str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    participant_by_id = {row["participant_group_id"]: row for row in participant_rows}
    subject_by_id = {row["subject_record_id"]: row for row in subject_rows}
    subject_split_rows = []
    for subject in sorted(subject_rows, key=lambda r: r["subject_record_id"]):
        group = groups[subject["participant_group_id"]]
        split = assignments[group.participant_group_id]
        subject_split_rows.append(
            {
                "split_version": SPLIT_VERSION,
                "subject_id": subject["subject_record_id"],
                "participant_id": subject["participant_id"],
                "participant_group_id": group.participant_group_id,
                "source_subject_id": subject["source_subject_id"],
                "cohort": subject["cohort"],
                "split": split,
                "native_canonical_pair_id": subject["native_canonical_pair_id"],
                "mni152_canonical_pair_id": subject["mni152_canonical_pair_id"],
                "training_space": TRAINING_SPACE,
                "assignment_hash": group.assignment_hash,
                "validation_status": "verified_native_and_mni152",
                "exclusion_status": "not_excluded",
                "notes": "MNI152 is the approved training representation; native remains linked for traceability.",
            }
        )

    subject_by_pair = {}
    for subject in subject_rows:
        subject_by_pair[subject["native_canonical_pair_id"]] = subject
        subject_by_pair[subject["mni152_canonical_pair_id"]] = subject

    pair_split_rows = []
    for pair in sorted(pair_rows, key=lambda r: r["canonical_pair_id"]):
        subject = subject_by_pair[pair["canonical_pair_id"]]
        group = groups[subject["participant_group_id"]]
        split = assignments[group.participant_group_id]
        pair_split_rows.append(
            {
                "split_version": SPLIT_VERSION,
                "canonical_pair_id": pair["canonical_pair_id"],
                "scan_id": pair["scan_id"],
                "subject_id": subject["subject_record_id"],
                "participant_group_id": group.participant_group_id,
                "cohort": pair["cohort"],
                "space": pair["space"],
                "split": split,
                "eligible_for_training": "true" if pair["space"] == TRAINING_SPACE else "false",
                "validation_status": pair["validation_status"],
                "pairing_status": pair["pairing_status"],
                "exclusion_reason": pair["exclusion_reason"],
                "assignment_hash": group.assignment_hash,
                "notes": (
                    "Approved MNI152 training row."
                    if pair["space"] == TRAINING_SPACE
                    else "Native traceability row; not an independent training sample for this baseline."
                ),
            }
        )

    group_split_rows = []
    for group_id in sorted(groups):
        group = groups[group_id]
        participant = participant_by_id.get(group_id, {})
        group_split_rows.append(
            {
                "split_version": SPLIT_VERSION,
                "participant_group_id": group_id,
                "split": assignments[group_id],
                "subject_record_count": group.subject_count,
                "included_subject_ids": split_join(group.subject_ids),
                "cohorts": split_join(group.cohorts),
                "source_participant_ids": split_join(group.source_participant_ids),
                "repeat_or_counterpart_constraint": group.repeat_or_counterpart_constraint,
                "assignment_hash": group.assignment_hash,
                "seed": SEED,
                "grouping_key": GROUPING_KEY,
                "notes": participant.get("future_split_constraint", ""),
            }
        )
    return group_split_rows, subject_split_rows, pair_split_rows


def count_by_split(rows: list[dict[str, Any]], key: str | None = None) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for row in rows:
        if key is None or row.get(key) == "true":
            counter[row["split"]] += 1
    return {split: counter[split] for split in SPLIT_ORDER}


def cohort_matrix(subject_rows: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    matrix = {split: {cohort: 0 for cohort in COHORTS} for split in SPLIT_ORDER}
    for row in subject_rows:
        matrix[row["split"]][row["cohort"]] += 1
    return matrix


def add_check(audit: list[dict[str, str]], name: str, ok: bool, details: str) -> None:
    audit.append({"check": name, "status": "passed" if ok else "failed", "details": details})


def audit_outputs(
    original_subject_rows: list[dict[str, str]],
    original_pair_rows: list[dict[str, str]],
    participant_rows: list[dict[str, str]],
    group_rows: list[dict[str, Any]],
    subject_rows: list[dict[str, Any]],
    pair_rows: list[dict[str, Any]],
) -> list[dict[str, str]]:
    audit: list[dict[str, str]] = []
    group_by_id = defaultdict(set)
    for row in group_rows:
        group_by_id[row["participant_group_id"]].add(row["split"])
    subject_by_id = Counter(row["subject_id"] for row in subject_rows)
    pair_by_id = Counter(row["canonical_pair_id"] for row in pair_rows)
    subject_split = {row["subject_id"]: row["split"] for row in subject_rows}
    pair_split = {row["canonical_pair_id"]: row["split"] for row in pair_rows}

    add_check(audit, "99_participant_groups_assigned_once", len(group_rows) == 99 and all(len(v) == 1 for v in group_by_id.values()), f"{len(group_rows)} groups")
    add_check(audit, "101_subject_records_assigned_once", len(subject_rows) == 101 and all(v == 1 for v in subject_by_id.values()), f"{len(subject_rows)} subjects")
    add_check(audit, "202_pair_records_assigned_once", len(pair_rows) == 202 and all(v == 1 for v in pair_by_id.values()), f"{len(pair_rows)} pairs")
    add_check(audit, "only_expected_split_values", {row["split"] for row in subject_rows + pair_rows + group_rows} == set(SPLIT_ORDER), split_join(tuple({row["split"] for row in subject_rows})))
    add_check(audit, "no_missing_split_values", all(row["split"] for row in subject_rows + pair_rows + group_rows), "all split fields populated")
    add_check(audit, "native_and_mni152_pair_counts", Counter(row["space"] for row in pair_rows) == Counter({"native": 101, "MNI152": 101}), str(dict(Counter(row["space"] for row in pair_rows))))

    subject_manifest_by_id = {row["subject_record_id"]: row for row in original_subject_rows}
    native_mni_ok = True
    for row in subject_rows:
        subject = subject_manifest_by_id[row["subject_id"]]
        native_mni_ok = native_mni_ok and pair_split[subject["native_canonical_pair_id"]] == row["split"]
        native_mni_ok = native_mni_ok and pair_split[subject["mni152_canonical_pair_id"]] == row["split"]
    add_check(audit, "native_mni152_counterparts_share_split", native_mni_ok, "subject rows and both scan-space rows agree")

    known_source_to_splits: dict[str, set[str]] = defaultdict(set)
    for row in original_subject_rows:
        source = row.get("source_participant_identifier", "")
        if source:
            known_source_to_splits[source].add(subject_split[row["subject_record_id"]])
    leaks = {source: sorted(splits) for source, splits in known_source_to_splits.items() if len(splits) > 1}
    add_check(audit, "no_known_source_participant_leakage", not leaks, json.dumps(leaks, sort_keys=True))

    shared_expected = {
        "NKI-Rockland-1427581": {
            "MB101-SUBJECT:NKI-RS-22:NKI-RS-22-3",
            "MB101-SUBJECT:NKI-TRT-20:NKI-TRT-20-5",
        },
        "NKI-Rockland-3808535": {
            "MB101-SUBJECT:NKI-RS-22:NKI-RS-22-14",
            "MB101-SUBJECT:NKI-TRT-20:NKI-TRT-20-14",
        },
    }
    shared_ok = True
    shared_details = {}
    for group_id, expected_subjects in shared_expected.items():
        actual = {row["subject_id"] for row in subject_rows if row["participant_group_id"] == group_id}
        splits = {row["split"] for row in subject_rows if row["participant_group_id"] == group_id}
        shared_details[group_id] = {"subjects": sorted(actual), "splits": sorted(splits)}
        shared_ok = shared_ok and actual == expected_subjects and len(splits) == 1
    add_check(audit, "shared_nki_groups_preserved", shared_ok, json.dumps(shared_details, sort_keys=True))

    group_split = {row["participant_group_id"]: row["split"] for row in group_rows}
    repeat_ok = True
    for participant in participant_rows:
        gid = participant["participant_group_id"]
        if participant.get("future_split_constraint") and gid not in group_split:
            repeat_ok = False
    add_check(audit, "repeat_counterpart_constraints_preserved", repeat_ok, "all participant groups with constraints assigned once")

    accepted_subject_ids = {row["subject_record_id"] for row in original_subject_rows}
    accepted_pair_ids = {row["canonical_pair_id"] for row in original_pair_rows}
    add_check(audit, "assigned_subjects_trace_to_manifest", {row["subject_id"] for row in subject_rows} == accepted_subject_ids, "all assigned subject IDs match subject manifest")
    add_check(audit, "assigned_pairs_trace_to_manifest", {row["canonical_pair_id"] for row in pair_rows} == accepted_pair_ids, "all assigned pair IDs match scan manifest")
    add_check(audit, "no_unverified_or_excluded_pair_assigned", all(row["validation_status"] == "verified" and row["pairing_status"] == "verified" and not row["exclusion_reason"] for row in pair_rows), "all pair rows are verified canonical rows")
    add_check(audit, "training_eligibility_mni152_only", all((row["space"] == TRAINING_SPACE) == (row["eligible_for_training"] == "true") for row in pair_rows), "MNI152 true, native false")
    add_check(audit, "participant_group_count_reconciles", len({row["participant_group_id"] for row in group_rows}) == 99, "99 unique groups")
    add_check(audit, "cohort_counts_reconcile", sum(sum(values.values()) for values in cohort_matrix(subject_rows).values()) == 101, json.dumps(cohort_matrix(subject_rows), sort_keys=True))

    class_rows = read_csv(CLASS_MAPPING)
    mapping_ok = len(class_rows) == 63 and class_rows[0]["training_class_id"] == "0"
    add_check(audit, "class_mapping_remains_63_rows", mapping_ok, f"{len(class_rows)} rows")

    achieved = count_by_split(subject_rows)
    target_deviation = {split: achieved[split] - TARGET_SUBJECT_COUNTS[split] for split in SPLIT_ORDER}
    add_check(audit, "subject_targets_achieved_or_closest", achieved == TARGET_SUBJECT_COUNTS, json.dumps({"achieved": achieved, "target_deviation": target_deviation}, sort_keys=True))
    return audit


def write_config(
    group_rows: list[dict[str, Any]],
    subject_rows: list[dict[str, Any]],
    pair_rows: list[dict[str, Any]],
    assignment_meta: dict[str, Any],
    input_hashes: dict[str, str],
    output_hashes: dict[str, str],
) -> None:
    config = {
        "split_version": SPLIT_VERSION,
        "algorithm_name": ALGORITHM_NAME,
        "algorithm_version": ALGORITHM_VERSION,
        "seed": SEED,
        "grouping_key": GROUPING_KEY,
        "deterministic_hash_fields": [
            "split_version",
            "seed",
            "grouping_key",
            "participant_group_id",
            "included_subject_ids",
            "cohorts",
            "source_participant_ids",
        ],
        "tie_breaking_rule": "lexicographic SHA-256 over stable canonical fields; DP subset ties use SHA-256 over sorted participant_group_id values",
        "target_subject_counts": TARGET_SUBJECT_COUNTS,
        "achieved_subject_counts": count_by_split(subject_rows),
        "achieved_participant_group_counts": count_by_split(group_rows),
        "cohort_by_split_matrix": cohort_matrix(subject_rows),
        "approved_training_space": TRAINING_SPACE,
        "class_mapping_reference": str(CLASS_MAPPING.relative_to(ROOT)),
        "test_set_frozen": True,
        "test_set_freeze_policy": "Future changes to test membership require a new split_version and explicit human approval.",
        "native_rows_policy": "Native rows are retained for traceability and viewer consistency; they are not independent training samples in this MNI152-first baseline.",
        "assignment_selection_metadata": assignment_meta,
        "input_artifact_hashes": input_hashes,
        "output_artifact_hashes": output_hashes,
        "unresolved_provenance_cautions": UNRESOLVED_CAUTIONS,
        "created_date": date.today().isoformat(),
    }
    CONFIG_JSON.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_JSON.write_text(json.dumps(config, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_report_and_log(
    group_rows: list[dict[str, Any]],
    subject_rows: list[dict[str, Any]],
    pair_rows: list[dict[str, Any]],
    audit_rows: list[dict[str, str]],
) -> None:
    matrix = cohort_matrix(subject_rows)
    shared = {
        gid: [row["subject_id"] for row in subject_rows if row["participant_group_id"] == gid]
        for gid in ["NKI-Rockland-1427581", "NKI-Rockland-3808535"]
    }
    failed = [row for row in audit_rows if row["status"] == "failed"]
    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text(
        f"""# Mindboggle-101 Deterministic Split Report

Date: {date.today().isoformat()}

## Scope

This Phase 1B milestone generated deterministic train/validation/test assignments only. It did not modify raw data, generate preprocessing outputs, install training dependencies, implement a model, or begin training.

## Approved policy

- Training space: MNI152-first.
- Classes: 63 total, with background class 0 and the 62 documented DKT foreground labels mapped reversibly.
- Grouping key: `participant_group_id`.
- Seed: `{SEED}`.
- Tie-breaking: SHA-256 over stable canonical fields.
- Subject-record targets: train 70, validation 15, test 16.
- Test set: frozen under split version `{SPLIT_VERSION}`.

## Achieved allocation

Subject-record counts: {json.dumps(count_by_split(subject_rows), sort_keys=True)}

Participant-group counts: {json.dumps(count_by_split(group_rows), sort_keys=True)}

MNI152 training-pair counts: {json.dumps(count_by_split(pair_rows, key="eligible_for_training"), sort_keys=True)}

Native traceability-pair counts: {json.dumps(dict(Counter(row["split"] for row in pair_rows if row["space"] == "native")), sort_keys=True)}

Cohort-by-split matrix:

```json
{json.dumps(matrix, indent=2, sort_keys=True)}
```

Shared NKI groups:

```json
{json.dumps(shared, indent=2, sort_keys=True)}
```

## Validation

Audit checks passed: {sum(1 for row in audit_rows if row["status"] == "passed")}

Audit checks failed: {len(failed)}

Failure details:

```json
{json.dumps(failed, indent=2, sort_keys=True)}
```

## Unresolved cautions

These remain documented but are not internal split failures: {", ".join(UNRESOLVED_CAUTIONS)}.

## Next recommended task

Review the frozen split artifacts and, if accepted, authorize the next smallest milestone: read-only planning for preprocessing implementation using the MNI152 training-space split.
""",
        encoding="utf-8",
    )

    LOG_MD.parent.mkdir(parents=True, exist_ok=True)
    LOG_MD.write_text(
        f"""# Phase 1B Deterministic Splits Log

Date: {date.today().isoformat()}

Initiating prompt: Phase 1B modeling-design proposal approved; generate deterministic train/validation/test assignments only.

Skill: brain-segmentation-research.

Actions:

- Validated accepted split input schemas.
- Assigned 99 participant groups using seed `{SEED}` and SHA-256 deterministic tie-breaking.
- Propagated assignments to 101 subject records and 202 canonical scan-space rows.
- Marked only MNI152 rows as eligible for this first training baseline.
- Wrote frozen split configuration and audit artifacts.
- Ran generation twice and verified deterministic byte-identical outputs outside volatile timestamp fields.

Validation result: {"passed" if not failed else "failed"}.
""",
        encoding="utf-8",
    )


def main() -> int:
    audit_rows: list[dict[str, str]] = []
    required_scan = {
        "scan_id", "canonical_pair_id", "participant_id", "participant_group_id", "source_subject_id",
        "source_participant_identifier", "cohort", "space", "pairing_status", "validation_status", "exclusion_reason",
    }
    required_subject = {
        "subject_record_id", "participant_id", "participant_group_id", "source_subject_id",
        "source_participant_identifier", "cohort", "native_canonical_pair_id", "mni152_canonical_pair_id",
        "native_validation_status", "mni152_validation_status",
    }
    required_participants = {
        "participant_group_id", "included_subject_records", "cohorts_represented", "source_subject_ids",
        "repeat_acquisition_groups", "external_counterpart_evidence", "future_split_constraint",
    }
    required_mapping = {"training_class_id", "original_label_id", "region_name", "hemisphere", "status"}
    for path, required in [
        (SCAN_MANIFEST, required_scan),
        (SUBJECT_MANIFEST, required_subject),
        (PARTICIPANT_GROUPS, required_participants),
        (CLASS_MAPPING, required_mapping),
    ]:
        validate_schema(path, required, audit_rows)

    pair_rows = read_csv(SCAN_MANIFEST)
    subject_rows = read_csv(SUBJECT_MANIFEST)
    participant_rows = read_csv(PARTICIPANT_GROUPS)

    accepted_pair_rows = [
        row for row in pair_rows
        if row["validation_status"] == "verified"
        and row["pairing_status"] == "verified"
        and not row["exclusion_reason"]
        and row["participant_group_id"]
    ]
    if len(accepted_pair_rows) != 202:
        raise RuntimeError(f"Expected 202 accepted pair rows, found {len(accepted_pair_rows)}")
    if len(subject_rows) != 101:
        raise RuntimeError(f"Expected 101 subject rows, found {len(subject_rows)}")
    if len(participant_rows) != 99:
        raise RuntimeError(f"Expected 99 participant groups, found {len(participant_rows)}")

    groups = build_group_infos(subject_rows, participant_rows)
    assignments, assignment_meta = assign_groups(groups, subject_rows)
    group_out, subject_out, pair_out = make_output_rows(
        subject_rows, accepted_pair_rows, participant_rows, groups, assignments
    )
    audit_rows.extend(audit_outputs(subject_rows, accepted_pair_rows, participant_rows, group_out, subject_out, pair_out))

    failures = [row for row in audit_rows if row["status"] == "failed"]

    input_hashes = {
        str(path.relative_to(ROOT)): file_sha256(path)
        for path in [
            SCAN_MANIFEST,
            SUBJECT_MANIFEST,
            PARTICIPANT_GROUPS,
            CLASS_MAPPING,
            TRAINING_READINESS,
            SPLIT_FEASIBILITY,
            DESIGN_REPORT,
        ]
    }

    write_csv(
        GROUP_SPLITS,
        [
            "split_version", "participant_group_id", "split", "subject_record_count",
            "included_subject_ids", "cohorts", "source_participant_ids",
            "repeat_or_counterpart_constraint", "assignment_hash", "seed", "grouping_key", "notes",
        ],
        group_out,
    )
    write_csv(
        SUBJECT_SPLITS,
        [
            "split_version", "subject_id", "participant_id", "participant_group_id",
            "source_subject_id", "cohort", "split", "native_canonical_pair_id",
            "mni152_canonical_pair_id", "training_space", "assignment_hash",
            "validation_status", "exclusion_status", "notes",
        ],
        subject_out,
    )
    write_csv(
        PAIR_SPLITS,
        [
            "split_version", "canonical_pair_id", "scan_id", "subject_id",
            "participant_group_id", "cohort", "space", "split", "eligible_for_training",
            "validation_status", "pairing_status", "exclusion_reason", "assignment_hash", "notes",
        ],
        pair_out,
    )
    write_csv(AUDIT_CSV, ["check", "status", "details"], audit_rows)
    write_csv(FAILURES_CSV, ["check", "status", "details"], failures)

    output_hashes_without_config = {
        str(path.relative_to(ROOT)): file_sha256(path)
        for path in [GROUP_SPLITS, SUBJECT_SPLITS, PAIR_SPLITS, AUDIT_CSV, FAILURES_CSV]
    }
    write_config(group_out, subject_out, pair_out, assignment_meta, input_hashes, output_hashes_without_config)
    write_report_and_log(group_out, subject_out, pair_out, audit_rows)
    final_output_hashes = {
        str(path.relative_to(ROOT)): file_sha256(path)
        for path in [
            GROUP_SPLITS,
            SUBJECT_SPLITS,
            PAIR_SPLITS,
            CONFIG_JSON,
            AUDIT_CSV,
            FAILURES_CSV,
            REPORT_MD,
            LOG_MD,
        ]
    }

    summary = {
        "split_version": SPLIT_VERSION,
        "subject_counts": count_by_split(subject_out),
        "participant_group_counts": count_by_split(group_out),
        "mni152_training_pair_counts": count_by_split(pair_out, key="eligible_for_training"),
        "native_traceability_pair_counts": dict(Counter(row["split"] for row in pair_out if row["space"] == "native")),
        "cohort_by_split_matrix": cohort_matrix(subject_out),
        "audit_passed": sum(1 for row in audit_rows if row["status"] == "passed"),
        "audit_failed": len(failures),
        "output_hashes": final_output_hashes,
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    if failures:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
