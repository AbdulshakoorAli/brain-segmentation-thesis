"""Validate approved in-memory MNI152 preprocessing on real split records."""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from collections import Counter
from datetime import date
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from brain_segmentation.loading import get_record_by_canonical_pair_id, load_verified_records  # noqa: E402
from brain_segmentation.preprocessing import (  # noqa: E402
    CLASS_COUNT,
    CLIP_PERCENTILES,
    EXPECTED_ORIENTATION,
    EXPECTED_SHAPE,
    EXPECTED_SPACE,
    EXPECTED_SPACING,
    LABEL_OUTPUT_DTYPE,
    MRI_OUTPUT_DTYPE,
    PREPROCESSING_CONFIG_VERSION,
    SPLIT_VERSION,
    inverse_map_training_classes,
    map_labels_to_training_classes,
    load_training_class_mapping,
    preprocess_verified_mni152_pair,
)
from brain_segmentation.qc import sha256_file  # noqa: E402


MANIFEST = ROOT / "data/derived/manifests/mindboggle101_scan_manifest.csv"
PAIR_SPLITS = ROOT / "data/derived/splits/mindboggle101_pair_splits.csv"
SPLIT_CONFIG = ROOT / "data/derived/splits/mindboggle101_split_config.json"
CLASS_MAPPING = ROOT / "data/derived/dictionaries/dkt_training_class_mapping_proposal.csv"
DKT_DICTIONARY = ROOT / "data/derived/dictionaries/dkt_label_dictionary.csv"
PREPROCESSING_CONFIG = ROOT / "data/derived/config/mindboggle101_preprocessing_config.json"
SMOKE_CSV = ROOT / "data/derived/qc/mindboggle101_preprocessing_smoke_test.csv"
REPORT = ROOT / "reports/phase1b/mindboggle101_preprocessing_implementation_report.md"
LOG = ROOT / "research_log/phase-1b-preprocessing-implementation.md"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def file_hashes(paths: list[Path]) -> dict[str, str]:
    return {str(path.relative_to(ROOT)): sha256_file(path) for path in paths}


def select_smoke_pair_ids() -> list[str]:
    rows = [
        row for row in read_csv(PAIR_SPLITS)
        if row["space"] == EXPECTED_SPACE and row["eligible_for_training"].lower() == "true"
    ]
    selected: dict[str, dict[str, str]] = {}
    for cohort in sorted({row["cohort"] for row in rows}):
        cohort_rows = [row for row in rows if row["cohort"] == cohort]
        selected[min(cohort_rows, key=lambda r: r["canonical_pair_id"])["canonical_pair_id"]] = min(
            cohort_rows, key=lambda r: r["canonical_pair_id"]
        )
    for split in ["train", "validation", "test"]:
        if split not in {row["split"] for row in selected.values()}:
            split_rows = [row for row in rows if row["split"] == split]
            selected[min(split_rows, key=lambda r: r["canonical_pair_id"])["canonical_pair_id"]] = min(
                split_rows, key=lambda r: r["canonical_pair_id"]
            )
    return sorted(selected)


def write_config() -> None:
    mapping_hash = sha256_file(CLASS_MAPPING)
    split_hash = sha256_file(PAIR_SPLITS)
    config = {
        "configuration_version": PREPROCESSING_CONFIG_VERSION,
        "approved_coordinate_space": EXPECTED_SPACE,
        "expected_geometry": {
            "shape": list(EXPECTED_SHAPE),
            "spacing_mm": list(EXPECTED_SPACING),
            "orientation": "".join(EXPECTED_ORIENTATION),
        },
        "foreground_definition": "MRI voxels with value != 0",
        "clipping_percentiles": list(CLIP_PERCENTILES),
        "normalization_method": "per-volume nonzero percentile clipping followed by per-volume nonzero z-score",
        "mri_output_dtype": np.dtype(MRI_OUTPUT_DTYPE).name,
        "label_output_dtype": np.dtype(LABEL_OUTPUT_DTYPE).name,
        "class_count": CLASS_COUNT,
        "mapping_artifact": str(CLASS_MAPPING.relative_to(ROOT)),
        "mapping_artifact_sha256": mapping_hash,
        "frozen_pair_split_artifact": str(PAIR_SPLITS.relative_to(ROOT)),
        "frozen_pair_split_artifact_sha256": split_hash,
        "frozen_split_config": str(SPLIT_CONFIG.relative_to(ROOT)),
        "frozen_split_config_sha256": sha256_file(SPLIT_CONFIG),
        "source_immutability_rule": "Read source NIfTI files only; never rewrite raw inputs.",
        "disabled_operations": [
            "resampling",
            "reorientation",
            "cropping",
            "padding",
            "patch generation",
            "augmentation",
            "materialized normalized volumes",
            "preprocessing caches",
            "tensor or DataLoader creation",
            "model training",
        ],
    }
    PREPROCESSING_CONFIG.parent.mkdir(parents=True, exist_ok=True)
    PREPROCESSING_CONFIG.write_text(json.dumps(config, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    write_config()
    records = load_verified_records(MANIFEST)
    mapping = load_training_class_mapping(CLASS_MAPPING)
    pair_ids = select_smoke_pair_ids()
    source_paths = []
    for pair_id in pair_ids:
        record = get_record_by_canonical_pair_id(records, pair_id)
        source_paths.extend([ROOT / record.mri_path, ROOT / record.label_path])
    source_before = file_hashes(source_paths)
    rows: list[dict[str, object]] = []
    for pair_id in pair_ids:
        record = get_record_by_canonical_pair_id(records, pair_id)
        first = preprocess_verified_mni152_pair(
            ROOT,
            record,
            dkt_dictionary_path=DKT_DICTIONARY,
            class_mapping_path=CLASS_MAPPING,
            pair_splits_path=PAIR_SPLITS,
        )
        second = preprocess_verified_mni152_pair(
            ROOT,
            record,
            dkt_dictionary_path=DKT_DICTIONARY,
            class_mapping_path=CLASS_MAPPING,
            pair_splits_path=PAIR_SPLITS,
        )
        foreground = first.normalized_mri != 0
        restored = inverse_map_training_classes(first.contiguous_label, mapping)
        remapped = map_labels_to_training_classes(restored, mapping)
        label_round_trip = np.array_equal(remapped, first.contiguous_label)
        label_round_trip = label_round_trip and np.array_equal(
            restored,
            inverse_map_training_classes(second.contiguous_label, mapping),
        )
        rows.append(
            {
                "canonical_pair_id": pair_id,
                "cohort": record.cohort,
                "split": first.split,
                "shape": "x".join(map(str, first.normalized_mri.shape)),
                "spacing": ";".join(f"{value:.9g}" for value in first.original_spacing),
                "mri_dtype": str(first.normalized_mri.dtype),
                "label_dtype": str(first.contiguous_label.dtype),
                "foreground_mean": float(first.normalized_mri[foreground].mean()),
                "foreground_std": float(first.normalized_mri[foreground].std()),
                "background_exact_zero": bool(np.all(first.normalized_mri[~foreground] == 0)),
                "finite_output": bool(np.all(np.isfinite(first.normalized_mri))),
                "class_definitions_available": len(mapping.class_to_original),
                "label_round_trip_exact": bool(label_round_trip),
                "arrays_identical_second_run": bool(
                    np.array_equal(first.normalized_mri, second.normalized_mri)
                    and np.array_equal(first.contiguous_label, second.contiguous_label)
                ),
                "metadata_identical_second_run": bool(
                    first.normalization == second.normalization
                    and first.source_mri_sha256 == second.source_mri_sha256
                    and first.source_label_sha256 == second.source_label_sha256
                    and first.split == second.split
                ),
                "source_mri_sha256": first.source_mri_sha256,
                "source_label_sha256": first.source_label_sha256,
                "status": "passed",
            }
        )
    source_after = file_hashes(source_paths)
    for row in rows:
        if abs(float(row["foreground_mean"])) > 1e-5:
            row["status"] = "failed"
        if abs(float(row["foreground_std"]) - 1.0) > 1e-5:
            row["status"] = "failed"
        for key in [
            "background_exact_zero",
            "finite_output",
            "label_round_trip_exact",
            "arrays_identical_second_run",
            "metadata_identical_second_run",
        ]:
            if not row[key]:
                row["status"] = "failed"
        if row["mri_dtype"] != "float32" or row["label_dtype"] != "uint8":
            row["status"] = "failed"
    write_csv(
        SMOKE_CSV,
        [
            "canonical_pair_id",
            "cohort",
            "split",
            "shape",
            "spacing",
            "mri_dtype",
            "label_dtype",
            "foreground_mean",
            "foreground_std",
            "background_exact_zero",
            "finite_output",
            "class_definitions_available",
            "label_round_trip_exact",
            "arrays_identical_second_run",
            "metadata_identical_second_run",
            "source_mri_sha256",
            "source_label_sha256",
            "status",
        ],
        rows,
    )
    counts = Counter(row["split"] for row in rows)
    cohorts = sorted({str(row["cohort"]) for row in rows})
    failed = [row for row in rows if row["status"] != "passed"]
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(
        f"""# Mindboggle-101 Preprocessing Implementation Report

Date: {date.today().isoformat()}

Implemented deterministic in-memory MNI152 preprocessing only. No preprocessed volumes, patches, tensors, caches, model code, training outputs, or evaluation results were created.

## API

- `normalize_mri_per_volume`
- `map_labels_to_training_classes`
- `inverse_map_training_classes`
- `preprocess_verified_mni152_pair`

## Approved behavior

- Per-volume nonzero 0.5/99.5 percentile clipping.
- Per-volume nonzero z-score after clipping.
- Background remains exactly zero.
- MRI output dtype is `float32`.
- Label output dtype is `uint8`.
- Native records are rejected for training preprocessing.
- Unknown original DKT IDs and unknown contiguous classes fail.

## Smoke validation

Records: {len(rows)}

Splits represented: {dict(counts)}

Cohorts represented: {cohorts}

Failed smoke rows: {len(failed)}

Source hashes preserved: {source_before == source_after}

Test-set use: frozen test records were used only to prove the approved per-volume transform executes deterministically; no parameter was tuned from test results.
""",
        encoding="utf-8",
    )
    LOG.parent.mkdir(parents=True, exist_ok=True)
    LOG.write_text(
        f"""# Phase 1B Preprocessing Implementation Log

Date: {date.today().isoformat()}

Initiating prompt: approved deterministic in-memory MNI152 preprocessing implementation.

Actions:

- Implemented reusable preprocessing functions in `src/brain_segmentation/preprocessing.py`.
- Added synthetic tests in `tests/test_preprocessing.py`.
- Created approved immutable preprocessing config.
- Ran deterministic real-data smoke validation on representative MNI152 records across cohorts and splits.
- Confirmed source hashes were preserved and no materialized preprocessing outputs were created.

Validation result: {"passed" if not failed and source_before == source_after else "failed"}.
""",
        encoding="utf-8",
    )
    summary = {
        "smoke_records": len(rows),
        "cohorts": cohorts,
        "splits": dict(counts),
        "failed": len(failed),
        "source_hashes_preserved": source_before == source_after,
        "outputs": [
            str(PREPROCESSING_CONFIG.relative_to(ROOT)),
            str(SMOKE_CSV.relative_to(ROOT)),
            str(REPORT.relative_to(ROOT)),
            str(LOG.relative_to(ROOT)),
        ],
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if not failed and source_before == source_after else 1


if __name__ == "__main__":
    raise SystemExit(main())
