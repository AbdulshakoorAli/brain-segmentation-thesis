"""Framework-independent lazy access to frozen Mindboggle-101 MNI152 training records.

This module intentionally does not implement patch sampling, augmentation,
framework-specific Dataset classes, tensors, model code, training, or
segmentation evaluation. It enumerates frozen split metadata and lazily delegates
single-record loading/preprocessing to the accepted loader and preprocessing API.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Mapping

import numpy as np

from brain_segmentation.loading import CanonicalPairRecord, load_verified_records
from brain_segmentation.preprocessing import (
    CLASS_COUNT,
    EXPECTED_ORIENTATION,
    EXPECTED_SHAPE,
    EXPECTED_SPACE,
    EXPECTED_SPACING,
    PREPROCESSING_CONFIG_VERSION,
    SPLIT_VERSION,
    PreprocessedPair,
    PreprocessingError,
    preprocess_verified_mni152_pair,
)

VALID_SPLITS = ("train", "validation", "test")
TRAINING_DATA_ACCESS_VERSION = "phase1b-mni152-lazy-training-data-access-v1"


class TrainingDataError(ValueError):
    """Raised when frozen training-data access metadata is invalid."""


@dataclass(frozen=True)
class TrainingRecordMetadata:
    canonical_pair_id: str
    scan_id: str
    subject_id: str
    participant_id: str
    participant_group_id: str
    cohort: str
    split: str
    space: str
    mri_path: str
    label_path: str
    shape: tuple[int, int, int]
    spacing: tuple[float, float, float]
    orientation: str
    validation_status: str
    pairing_status: str
    exclusion_reason: str
    eligible_for_training: bool
    split_version: str
    assignment_hash: str
    source_subject_id: str
    source_participant_identifier: str


@dataclass(frozen=True)
class TrainingDataItem:
    normalized_mri: np.ndarray
    contiguous_label: np.ndarray
    canonical_pair_id: str
    scan_id: str
    subject_id: str
    participant_group_id: str
    cohort: str
    split: str
    space: str
    affine: np.ndarray
    shape: tuple[int, int, int]
    spacing: tuple[float, float, float]
    normalization: object
    mapping_version: str
    preprocessing_config_version: str
    training_data_access_version: str
    source_mri_path: str
    source_label_path: str
    source_mri_sha256: str
    source_label_sha256: str
    assignment_hash: str


@dataclass(frozen=True)
class _PairSplitRow:
    canonical_pair_id: str
    scan_id: str
    subject_id: str
    participant_group_id: str
    cohort: str
    space: str
    split: str
    eligible_for_training: bool
    validation_status: str
    pairing_status: str
    exclusion_reason: str
    split_version: str
    assignment_hash: str


def _parse_bool(value: str, *, field: str, pair_id: str) -> bool:
    normalized = value.strip().lower()
    if normalized == "true":
        return True
    if normalized == "false":
        return False
    raise TrainingDataError(f"Invalid boolean {field}={value!r} for {pair_id}")


def _parse_shape(value: str) -> tuple[int, int, int]:
    try:
        parsed = tuple(int(part) for part in value.split("x"))
    except Exception as exc:
        raise TrainingDataError(f"Malformed shape value: {value!r}") from exc
    if len(parsed) != 3:
        raise TrainingDataError(f"Malformed shape value: {value!r}")
    return parsed


def _parse_spacing(value: str) -> tuple[float, float, float]:
    try:
        parsed = tuple(float(part) for part in value.split(";"))
    except Exception as exc:
        raise TrainingDataError(f"Malformed spacing value: {value!r}") from exc
    if len(parsed) != 3:
        raise TrainingDataError(f"Malformed spacing value: {value!r}")
    return parsed


def _load_pair_split_rows(path: Path) -> dict[str, _PairSplitRow]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        rows = list(reader)
    required = {
        "split_version", "canonical_pair_id", "scan_id", "subject_id", "participant_group_id",
        "cohort", "space", "split", "eligible_for_training", "validation_status",
        "pairing_status", "exclusion_reason", "assignment_hash",
    }
    if reader.fieldnames is None or not required.issubset(set(reader.fieldnames)):
        missing = sorted(required - set(reader.fieldnames or []))
        raise TrainingDataError(f"Pair split file missing required fields: {missing}")
    parsed: dict[str, _PairSplitRow] = {}
    for row in rows:
        pair_id = row["canonical_pair_id"]
        if not pair_id:
            raise TrainingDataError("Pair split row has an empty canonical_pair_id")
        if pair_id in parsed:
            raise TrainingDataError(f"Duplicate canonical pair ID in split file: {pair_id}")
        split = row["split"]
        if split not in VALID_SPLITS:
            raise TrainingDataError(f"Invalid split {split!r} for {pair_id}")
        parsed[pair_id] = _PairSplitRow(
            canonical_pair_id=pair_id,
            scan_id=row["scan_id"],
            subject_id=row["subject_id"],
            participant_group_id=row["participant_group_id"],
            cohort=row["cohort"],
            space=row["space"],
            split=split,
            eligible_for_training=_parse_bool(row["eligible_for_training"], field="eligible_for_training", pair_id=pair_id),
            validation_status=row["validation_status"],
            pairing_status=row["pairing_status"],
            exclusion_reason=row["exclusion_reason"],
            split_version=row["split_version"],
            assignment_hash=row["assignment_hash"],
        )
    return parsed


def _make_metadata(record: CanonicalPairRecord, split_row: _PairSplitRow) -> TrainingRecordMetadata:
    if record.space != EXPECTED_SPACE or split_row.space != EXPECTED_SPACE:
        raise TrainingDataError(f"Native or non-MNI152 row reached training metadata: {record.canonical_pair_id}")
    if record.validation_status != "verified" or split_row.validation_status != "verified":
        raise TrainingDataError(f"Unverified record cannot be used for training access: {record.canonical_pair_id}")
    if record.pairing_status != "verified" or split_row.pairing_status != "verified":
        raise TrainingDataError(f"Unverified pair cannot be used for training access: {record.canonical_pair_id}")
    if split_row.exclusion_reason:
        raise TrainingDataError(f"Excluded record cannot be used for training access: {record.canonical_pair_id}")
    if not split_row.eligible_for_training:
        raise TrainingDataError(f"Ineligible row cannot be used for training access: {record.canonical_pair_id}")
    if split_row.split_version != SPLIT_VERSION:
        raise TrainingDataError(f"Unexpected split version for {record.canonical_pair_id}: {split_row.split_version}")
    return TrainingRecordMetadata(
        canonical_pair_id=record.canonical_pair_id,
        scan_id=record.scan_id,
        subject_id=split_row.subject_id,
        participant_id=record.participant_id,
        participant_group_id=record.participant_group_id,
        cohort=record.cohort,
        split=split_row.split,
        space=record.space,
        mri_path=record.mri_path,
        label_path=record.label_path,
        shape=_parse_shape(record.mri_dimensions),
        spacing=_parse_spacing(record.mri_voxel_spacing),
        orientation=record.mri_orientation,
        validation_status=record.validation_status,
        pairing_status=record.pairing_status,
        exclusion_reason=split_row.exclusion_reason,
        eligible_for_training=split_row.eligible_for_training,
        split_version=split_row.split_version,
        assignment_hash=split_row.assignment_hash,
        source_subject_id=record.source_subject_id,
        source_participant_identifier=record.source_participant_identifier,
    )


class MindboggleTrainingDataset:
    """Lazy framework-independent access to one frozen MNI152 split.

    Test split construction requires ``allow_frozen_test=True``. Test records are
    frozen and must not be used for development decisions, tuning,
    preprocessing-parameter changes, or model selection.
    """

    def __init__(
        self,
        project_root: Path,
        split: str,
        *,
        allow_frozen_test: bool = False,
        manifest_path: Path | None = None,
        pair_splits_path: Path | None = None,
        dkt_dictionary_path: Path | None = None,
        class_mapping_path: Path | None = None,
        preprocess_func: Callable[..., PreprocessedPair] = preprocess_verified_mni152_pair,
    ) -> None:
        if split not in VALID_SPLITS:
            raise TrainingDataError(f"Unknown split {split!r}; expected one of {VALID_SPLITS}")
        if split == "test" and not allow_frozen_test:
            raise TrainingDataError("Frozen test access requires allow_frozen_test=True")
        self.project_root = Path(project_root)
        self.split = split
        self.allow_frozen_test = allow_frozen_test
        self.manifest_path = Path(manifest_path) if manifest_path is not None else self.project_root / "data/derived/manifests/mindboggle101_scan_manifest.csv"
        self.pair_splits_path = Path(pair_splits_path) if pair_splits_path is not None else self.project_root / "data/derived/splits/mindboggle101_pair_splits.csv"
        self.dkt_dictionary_path = Path(dkt_dictionary_path) if dkt_dictionary_path is not None else self.project_root / "data/derived/dictionaries/dkt_label_dictionary.csv"
        self.class_mapping_path = Path(class_mapping_path) if class_mapping_path is not None else self.project_root / "data/derived/dictionaries/dkt_training_class_mapping_proposal.csv"
        self._preprocess_func = preprocess_func

        records = load_verified_records(self.manifest_path)
        self._records_by_id = {record.canonical_pair_id: record for record in records}
        if len(self._records_by_id) != len(records):
            raise TrainingDataError("Manifest contains duplicate canonical pair IDs")
        self._split_rows_by_id = _load_pair_split_rows(self.pair_splits_path)
        self._metadata_by_id: dict[str, TrainingRecordMetadata] = {}
        selected: list[TrainingRecordMetadata] = []

        for pair_id, split_row in self._split_rows_by_id.items():
            if split_row.eligible_for_training and split_row.space != EXPECTED_SPACE:
                raise TrainingDataError(f"Native or non-MNI152 row is marked training-eligible: {pair_id}")
            if split_row.space == EXPECTED_SPACE and split_row.eligible_for_training:
                if pair_id not in self._records_by_id:
                    raise TrainingDataError(f"Training-eligible split row has no verified manifest record: {pair_id}")
                metadata = _make_metadata(self._records_by_id[pair_id], split_row)
                self._metadata_by_id[pair_id] = metadata
                if split_row.split == split:
                    selected.append(metadata)

        for record in [record for record in records if record.space == EXPECTED_SPACE]:
            split_row = self._split_rows_by_id.get(record.canonical_pair_id)
            if split_row is None:
                raise TrainingDataError(f"Missing split assignment for MNI152 record: {record.canonical_pair_id}")
            if not split_row.eligible_for_training:
                raise TrainingDataError(f"MNI152 record is not training-eligible: {record.canonical_pair_id}")

        self._metadata = tuple(sorted(selected, key=lambda item: (item.cohort, item.participant_id, item.scan_id, item.canonical_pair_id)))
        self._index_by_pair_id = {item.canonical_pair_id: index for index, item in enumerate(self._metadata)}

    def __len__(self) -> int:
        return len(self._metadata)

    def __iter__(self) -> Iterable[TrainingRecordMetadata]:
        return iter(self._metadata)

    @property
    def metadata(self) -> tuple[TrainingRecordMetadata, ...]:
        return self._metadata

    def metadata_at(self, index: int) -> TrainingRecordMetadata:
        try:
            return self._metadata[index]
        except IndexError as exc:
            raise TrainingDataError(f"Index out of range for split {self.split}: {index}") from exc

    def get_metadata_by_canonical_pair_id(self, canonical_pair_id: str) -> TrainingRecordMetadata:
        if canonical_pair_id in self._index_by_pair_id:
            return self._metadata[self._index_by_pair_id[canonical_pair_id]]
        if canonical_pair_id in self._metadata_by_id:
            other = self._metadata_by_id[canonical_pair_id]
            raise TrainingDataError(f"Canonical pair {canonical_pair_id!r} belongs to split {other.split!r}, not {self.split!r}")
        if canonical_pair_id in self._split_rows_by_id:
            row = self._split_rows_by_id[canonical_pair_id]
            if row.space != EXPECTED_SPACE:
                raise TrainingDataError(f"Canonical pair {canonical_pair_id!r} is not an MNI152 training record")
            if not row.eligible_for_training:
                raise TrainingDataError(f"Canonical pair {canonical_pair_id!r} is not eligible for training")
        raise TrainingDataError(f"Unknown canonical pair ID: {canonical_pair_id}")

    def load_item(self, index: int) -> TrainingDataItem:
        return self.load_by_canonical_pair_id(self.metadata_at(index).canonical_pair_id)

    def load_by_canonical_pair_id(self, canonical_pair_id: str) -> TrainingDataItem:
        metadata = self.get_metadata_by_canonical_pair_id(canonical_pair_id)
        record = self._records_by_id[metadata.canonical_pair_id]
        try:
            preprocessed = self._preprocess_func(
                self.project_root,
                record,
                dkt_dictionary_path=self.dkt_dictionary_path,
                class_mapping_path=self.class_mapping_path,
                pair_splits_path=self.pair_splits_path,
            )
        except Exception as exc:
            if isinstance(exc, (TrainingDataError, PreprocessingError)):
                raise
            raise TrainingDataError(f"Preprocessing failed for {canonical_pair_id}: {type(exc).__name__}: {exc}") from exc
        if preprocessed.canonical_pair_id != metadata.canonical_pair_id:
            raise TrainingDataError("Preprocessing returned a different canonical_pair_id")
        if preprocessed.split != metadata.split:
            raise TrainingDataError("Preprocessing returned a conflicting split")
        return TrainingDataItem(
            normalized_mri=preprocessed.normalized_mri,
            contiguous_label=preprocessed.contiguous_label,
            canonical_pair_id=metadata.canonical_pair_id,
            scan_id=metadata.scan_id,
            subject_id=metadata.subject_id,
            participant_group_id=metadata.participant_group_id,
            cohort=metadata.cohort,
            split=metadata.split,
            space=metadata.space,
            affine=preprocessed.affine,
            shape=preprocessed.original_shape,
            spacing=preprocessed.original_spacing,
            normalization=preprocessed.normalization,
            mapping_version=preprocessed.mapping_version,
            preprocessing_config_version=preprocessed.preprocessing_config_version,
            training_data_access_version=TRAINING_DATA_ACCESS_VERSION,
            source_mri_path=preprocessed.source_mri_path,
            source_label_path=preprocessed.source_label_path,
            source_mri_sha256=preprocessed.source_mri_sha256,
            source_label_sha256=preprocessed.source_label_sha256,
            assignment_hash=metadata.assignment_hash,
        )

    def summary(self) -> dict[str, object]:
        cohort_counts: dict[str, int] = {}
        participant_groups = set()
        for item in self._metadata:
            cohort_counts[item.cohort] = cohort_counts.get(item.cohort, 0) + 1
            participant_groups.add(item.participant_group_id)
        return {
            "split": self.split,
            "record_count": len(self._metadata),
            "participant_group_count": len(participant_groups),
            "cohort_counts": dict(sorted(cohort_counts.items())),
            "expected_geometry": {"shape": EXPECTED_SHAPE, "spacing_mm": EXPECTED_SPACING, "orientation": "".join(EXPECTED_ORIENTATION)},
            "class_count": CLASS_COUNT,
            "preprocessing_version": PREPROCESSING_CONFIG_VERSION,
            "training_data_access_version": TRAINING_DATA_ACCESS_VERSION,
            "split_version": SPLIT_VERSION,
            "frozen_test_status": "requires_explicit_allow_frozen_test" if self.split == "test" else "not_test_split",
        }
