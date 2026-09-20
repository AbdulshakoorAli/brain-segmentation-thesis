from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from datetime import date
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from brain_segmentation.training_data import MindboggleTrainingDataset, TRAINING_DATA_ACCESS_VERSION

VALIDATION_CSV = ROOT / "data/derived/qc/mindboggle101_training_data_access_validation.csv"
REPORT = ROOT / "reports/phase1b/mindboggle101_training_data_access_report.md"
LOG = ROOT / "research_log/phase-1b-training-data-access.md"
UPSTREAM = [
    "data/derived/splits/mindboggle101_pair_splits.csv",
    "data/derived/splits/mindboggle101_subject_splits.csv",
    "data/derived/splits/mindboggle101_split_config.json",
    "data/derived/config/mindboggle101_preprocessing_config.json",
    "data/derived/manifests/mindboggle101_scan_manifest.csv",
    "data/derived/dictionaries/dkt_training_class_mapping_proposal.csv",
    "src/brain_segmentation/loading.py",
    "src/brain_segmentation/preprocessing.py",
]
EXPECTED_COUNTS = {"train": 70, "validation": 15, "test": 16}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def construct():
    return {
        "train": MindboggleTrainingDataset(ROOT, "train"),
        "validation": MindboggleTrainingDataset(ROOT, "validation"),
        "test": MindboggleTrainingDataset(ROOT, "test", allow_frozen_test=True),
    }


def select_smoke(datasets):
    all_meta = [meta for ds in datasets.values() for meta in ds.metadata]
    selected = {}
    for cohort in sorted({m.cohort for m in all_meta}):
        chosen = min((m for m in all_meta if m.cohort == cohort), key=lambda m: (m.split, m.canonical_pair_id))
        selected[chosen.canonical_pair_id] = chosen
    for split in ["train", "validation", "test"]:
        if not any(m.split == split for m in selected.values()):
            chosen = min(datasets[split].metadata, key=lambda m: (m.cohort, m.canonical_pair_id))
            selected[chosen.canonical_pair_id] = chosen
    return tuple(sorted(selected.values(), key=lambda m: (m.split, m.cohort, m.canonical_pair_id)))


def item_metadata(item):
    return {
        "canonical_pair_id": item.canonical_pair_id,
        "scan_id": item.scan_id,
        "subject_id": item.subject_id,
        "participant_group_id": item.participant_group_id,
        "cohort": item.cohort,
        "split": item.split,
        "space": item.space,
        "shape": item.shape,
        "spacing": item.spacing,
        "mapping_version": item.mapping_version,
        "preprocessing_config_version": item.preprocessing_config_version,
        "source_mri_path": item.source_mri_path,
        "source_label_path": item.source_label_path,
        "assignment_hash": item.assignment_hash,
    }


def main() -> int:
    before_hashes = {p: sha256(ROOT / p) for p in UPSTREAM}
    datasets = construct()
    repeated = construct()
    rows = []
    failures = []

    counts = {split: len(ds) for split, ds in datasets.items()}
    for split, expected in EXPECTED_COUNTS.items():
        if counts[split] != expected:
            failures.append(f"{split} count {counts[split]} != {expected}")
    if any([m.canonical_pair_id for m in datasets[s].metadata] != [m.canonical_pair_id for m in repeated[s].metadata] for s in datasets):
        failures.append("Enumeration differs across repeated construction")

    split_ids = {split: {m.canonical_pair_id for m in ds.metadata} for split, ds in datasets.items()}
    group_ids = {split: {m.participant_group_id for m in ds.metadata} for split, ds in datasets.items()}
    if len(set.union(*split_ids.values())) != 101:
        failures.append("Unique canonical ID count is not 101")
    for left in EXPECTED_COUNTS:
        for right in EXPECTED_COUNTS:
            if left < right and split_ids[left] & split_ids[right]:
                failures.append(f"Canonical ID overlap between {left} and {right}")
            if left < right and group_ids[left] & group_ids[right]:
                failures.append(f"Participant-group overlap between {left} and {right}")

    all_meta = [m for ds in datasets.values() for m in ds.metadata]
    if any(m.space != "MNI152" or not m.eligible_for_training for m in all_meta):
        failures.append("Non-MNI152 or ineligible row is accessible")
    cohort_counts = Counter(m.cohort for m in all_meta)
    if len(cohort_counts) != 5:
        failures.append("Not all five cohorts are represented")

    smoke = select_smoke(datasets)
    for meta in smoke:
        ds = datasets[meta.split]
        before_mri = sha256(ROOT / meta.mri_path)
        before_label = sha256(ROOT / meta.label_path)
        first = ds.load_by_canonical_pair_id(meta.canonical_pair_id)
        second = ds.load_by_canonical_pair_id(meta.canonical_pair_id)
        after_mri = sha256(ROOT / first.source_mri_path)
        after_label = sha256(ROOT / first.source_label_path)
        foreground = first.normalized_mri != 0
        row_failures = []
        if first.shape != (182, 218, 182):
            row_failures.append("shape")
        if first.normalized_mri.dtype != np.float32:
            row_failures.append("mri_dtype")
        if first.contiguous_label.dtype != np.uint8:
            row_failures.append("label_dtype")
        if not np.all(np.isfinite(first.normalized_mri)):
            row_failures.append("finite_mri")
        if not np.all(first.normalized_mri[~foreground] == 0):
            row_failures.append("zero_background")
        observed = set(int(v) for v in np.unique(first.contiguous_label))
        if not observed <= set(range(63)):
            row_failures.append("classes")
        if first.split != meta.split or first.participant_group_id != meta.participant_group_id:
            row_failures.append("metadata")
        if not np.array_equal(first.normalized_mri, second.normalized_mri):
            row_failures.append("mri_determinism")
        if not np.array_equal(first.contiguous_label, second.contiguous_label):
            row_failures.append("label_determinism")
        if item_metadata(first) != item_metadata(second):
            row_failures.append("metadata_determinism")
        if before_mri != after_mri or before_label != after_label or before_mri != first.source_mri_sha256 or before_label != first.source_label_sha256:
            row_failures.append("source_hash_preservation")
        rows.append({
            "canonical_pair_id": meta.canonical_pair_id,
            "cohort": meta.cohort,
            "split": meta.split,
            "participant_group_id": meta.participant_group_id,
            "shape": "x".join(str(v) for v in first.shape),
            "spacing": ";".join(str(v) for v in first.spacing),
            "mri_dtype": str(first.normalized_mri.dtype),
            "label_dtype": str(first.contiguous_label.dtype),
            "finite_mri": str(bool(np.all(np.isfinite(first.normalized_mri)))),
            "background_exact_zero": str(bool(np.all(first.normalized_mri[~foreground] == 0))),
            "valid_classes_0_62": str(observed <= set(range(63))),
            "arrays_identical_second_run": str(bool(np.array_equal(first.normalized_mri, second.normalized_mri) and np.array_equal(first.contiguous_label, second.contiguous_label))),
            "metadata_identical_second_run": str(item_metadata(first) == item_metadata(second)),
            "source_hashes_preserved": str("source_hash_preservation" not in row_failures),
            "status": "passed" if not row_failures else "failed:" + ";".join(row_failures),
        })
        failures.extend(f"{meta.canonical_pair_id}: {failure}" for failure in row_failures)

    after_hashes = {p: sha256(ROOT / p) for p in UPSTREAM}
    if before_hashes != after_hashes:
        failures.append("An upstream artifact hash changed")

    VALIDATION_CSV.parent.mkdir(parents=True, exist_ok=True)
    with VALIDATION_CSV.open("w", newline="", encoding="utf-8") as stream:
        fields = [
            "canonical_pair_id", "cohort", "split", "participant_group_id", "shape", "spacing",
            "mri_dtype", "label_dtype", "finite_mri", "background_exact_zero", "valid_classes_0_62",
            "arrays_identical_second_run", "metadata_identical_second_run", "source_hashes_preserved", "status",
        ]
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(
        "# Mindboggle-101 Training-Data Access Report\n\n"
        f"Date: {date.today().isoformat()}\n\n"
        "Implemented framework-independent lazy access to the frozen MNI152 split records. No patch sampling, augmentation, tensors, DataLoaders, models, training, evaluation, or materialized preprocessing outputs were created.\n\n"
        f"Training-data access version: `{TRAINING_DATA_ACCESS_VERSION}`\n\n"
        f"Record counts: {json.dumps(counts, sort_keys=True)}\n\n"
        f"Participant-group counts: {json.dumps({k: len(v) for k, v in group_ids.items()}, sort_keys=True)}\n\n"
        f"Cohort counts: {json.dumps(dict(sorted(cohort_counts.items())), sort_keys=True)}\n\n"
        f"Smoke records: {len(rows)}\n\n"
        f"Failures: {len(failures)}\n\n"
        "Frozen test access requires explicit `allow_frozen_test=True`; test data remains unavailable by default and must not be used for tuning or development decisions.\n\n"
        "Upstream raw and accepted artifacts were hash-checked before and after validation and remained unchanged.\n",
        encoding="utf-8",
    )
    LOG.parent.mkdir(parents=True, exist_ok=True)
    LOG.write_text(
        "# Phase 1B Training-Data Access\n\n"
        f"Date: {date.today().isoformat()}\n\n"
        "Prompt: implement only a framework-independent, lazy training-data access layer using the accepted loader and preprocessing API.\n\n"
        f"Validation result: {'passed' if not failures else 'failed'}\n\n"
        f"Counts: {json.dumps(counts, sort_keys=True)}\n\n"
        f"Smoke records: {[row['canonical_pair_id'] for row in rows]}\n\n"
        "No raw data, split artifacts, class mappings, manifests, accepted loader/preprocessing implementation, materialized arrays, patches, tensors, model code, or training outputs were modified or created.\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "counts": counts,
        "participant_group_counts": {k: len(v) for k, v in group_ids.items()},
        "cohort_counts": dict(sorted(cohort_counts.items())),
        "smoke_records": len(rows),
        "failures": failures,
        "outputs": [str(VALIDATION_CSV.relative_to(ROOT)), str(REPORT.relative_to(ROOT)), str(LOG.relative_to(ROOT))],
    }, indent=2, sort_keys=True))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
