"""In-memory preprocessing for approved Mindboggle-101 MNI152 pairs.

The functions in this module are deterministic and read-only. They do not
write NIfTI files, normalized arrays, patches, tensors, or caches.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

import nibabel as nib
import numpy as np

from brain_segmentation.loading import CanonicalPairRecord, load_verified_pair
from brain_segmentation.qc import AFFINE_ATOL, AFFINE_RTOL, sha256_file


PREPROCESSING_CONFIG_VERSION = "phase1b-mni152-inmemory-preprocessing-v1"
SPLIT_VERSION = "phase1b-1.0-seed20260831-participant_group_id-approved-20260920"
EXPECTED_SPACE = "MNI152"
EXPECTED_SHAPE = (182, 218, 182)
EXPECTED_SPACING = (1.0, 1.0, 1.0)
EXPECTED_ORIENTATION = ("L", "A", "S")
CLIP_PERCENTILES = (0.5, 99.5)
MRI_OUTPUT_DTYPE = np.float32
LABEL_OUTPUT_DTYPE = np.uint8
CLASS_COUNT = 63


class PreprocessingError(ValueError):
    """Raised when a record or array cannot be safely preprocessed."""


@dataclass(frozen=True)
class NormalizationParameters:
    foreground_voxel_count: int
    lower_percentile: float
    upper_percentile: float
    lower_clip_value: float
    upper_clip_value: float
    clipped_foreground_mean: float
    clipped_foreground_std: float


@dataclass(frozen=True)
class TrainingClassMapping:
    original_to_class: dict[int, int]
    class_to_original: dict[int, int]
    class_names: dict[int, str]
    mapping_version: str
    source_path: str


@dataclass(frozen=True)
class PairSplitAssignment:
    canonical_pair_id: str
    split: str
    eligible_for_training: bool
    split_version: str


@dataclass(frozen=True)
class PreprocessedPair:
    normalized_mri: np.ndarray
    contiguous_label: np.ndarray
    canonical_pair_id: str
    participant_group_id: str
    split: str
    affine: np.ndarray
    original_shape: tuple[int, int, int]
    original_spacing: tuple[float, float, float]
    normalization: NormalizationParameters
    mapping_version: str
    preprocessing_config_version: str
    source_mri_path: str
    source_label_path: str
    source_mri_sha256: str
    source_label_sha256: str


def _ensure_numeric_3d_mri(mri: np.ndarray) -> np.ndarray:
    array = np.asarray(mri)
    if array.ndim != 3:
        raise PreprocessingError(f"MRI must be 3D; got shape {array.shape}")
    if not np.issubdtype(array.dtype, np.number):
        raise PreprocessingError(f"MRI must be numeric; got dtype {array.dtype}")
    if not np.all(np.isfinite(array)):
        raise PreprocessingError("MRI contains non-finite values")
    return array


def normalize_mri_per_volume(
    mri: np.ndarray,
    *,
    lower_percentile: float = CLIP_PERCENTILES[0],
    upper_percentile: float = CLIP_PERCENTILES[1],
) -> tuple[np.ndarray, NormalizationParameters]:
    """Clip and z-score one MRI volume using nonzero voxels only.

    Background voxels, defined as exactly zero in the source MRI, remain exactly
    zero in the output. The input array is never modified in place.
    """
    array = _ensure_numeric_3d_mri(mri)
    foreground = array != 0
    count = int(np.count_nonzero(foreground))
    if count == 0:
        raise PreprocessingError("MRI normalization foreground is empty")
    values = array[foreground].astype(np.float64, copy=True)
    lower = float(np.percentile(values, lower_percentile))
    upper = float(np.percentile(values, upper_percentile))
    if not np.isfinite(lower) or not np.isfinite(upper) or upper < lower:
        raise PreprocessingError("MRI clipping percentiles are invalid")
    clipped = np.clip(values, lower, upper)
    mean = float(np.mean(clipped))
    std = float(np.std(clipped))
    if not np.isfinite(std) or std <= 0:
        raise PreprocessingError("MRI clipped foreground standard deviation is invalid or zero")
    output = np.zeros(array.shape, dtype=MRI_OUTPUT_DTYPE)
    output[foreground] = ((clipped - mean) / std).astype(MRI_OUTPUT_DTYPE)
    params = NormalizationParameters(
        foreground_voxel_count=count,
        lower_percentile=float(lower_percentile),
        upper_percentile=float(upper_percentile),
        lower_clip_value=lower,
        upper_clip_value=upper,
        clipped_foreground_mean=mean,
        clipped_foreground_std=std,
    )
    return output, params


def load_training_class_mapping(path: Path) -> TrainingClassMapping:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        rows = list(csv.DictReader(stream))
    original_to_class: dict[int, int] = {}
    class_to_original: dict[int, int] = {}
    class_names: dict[int, str] = {}
    for row in rows:
        class_id = int(row["training_class_id"])
        original_id = int(row["original_label_id"])
        if class_id in class_to_original:
            raise PreprocessingError(f"Duplicate training class ID: {class_id}")
        if original_id in original_to_class:
            raise PreprocessingError(f"Duplicate original DKT ID: {original_id}")
        class_to_original[class_id] = original_id
        original_to_class[original_id] = class_id
        class_names[class_id] = f"{row['hemisphere']} {row['region_name']}"
    expected = set(range(CLASS_COUNT))
    if set(class_to_original) != expected:
        raise PreprocessingError("Training class mapping must define contiguous classes 0-62")
    if class_to_original.get(0) != 0 or original_to_class.get(0) != 0:
        raise PreprocessingError("Background must map original ID 0 to class 0")
    return TrainingClassMapping(
        original_to_class=original_to_class,
        class_to_original=class_to_original,
        class_names=class_names,
        mapping_version=PREPROCESSING_CONFIG_VERSION,
        source_path=str(path),
    )


def _validate_integer_labels(label: np.ndarray) -> np.ndarray:
    array = np.asarray(label)
    if array.ndim != 3:
        raise PreprocessingError(f"Label volume must be 3D; got shape {array.shape}")
    if not np.all(np.isfinite(array)):
        raise PreprocessingError("Label volume contains non-finite values")
    if not np.all(array == np.rint(array)):
        raise PreprocessingError("Label volume contains non-integer values")
    return array.astype(np.int64, copy=False)


def map_labels_to_training_classes(label: np.ndarray, mapping: TrainingClassMapping) -> np.ndarray:
    """Map original DKT IDs to contiguous uint8 classes 0-62."""
    original = _validate_integer_labels(label)
    observed = {int(value) for value in np.unique(original)}
    unknown = sorted(observed - set(mapping.original_to_class))
    if unknown:
        raise PreprocessingError(f"Unknown original DKT label IDs: {unknown}")
    output = np.zeros(original.shape, dtype=LABEL_OUTPUT_DTYPE)
    for original_id, class_id in mapping.original_to_class.items():
        output[original == original_id] = class_id
    return output


def inverse_map_training_classes(classes: np.ndarray, mapping: TrainingClassMapping) -> np.ndarray:
    """Map contiguous classes 0-62 back to original DKT IDs."""
    class_array = _validate_integer_labels(classes)
    observed = {int(value) for value in np.unique(class_array)}
    unknown = sorted(observed - set(mapping.class_to_original))
    if unknown:
        raise PreprocessingError(f"Unknown contiguous class IDs: {unknown}")
    output = np.zeros(class_array.shape, dtype=np.int16)
    for class_id, original_id in mapping.class_to_original.items():
        output[class_array == class_id] = original_id
    return output


def load_pair_split_assignments(path: Path) -> dict[str, PairSplitAssignment]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        rows = list(csv.DictReader(stream))
    assignments: dict[str, PairSplitAssignment] = {}
    for row in rows:
        pair_id = row["canonical_pair_id"]
        if pair_id in assignments:
            raise PreprocessingError(f"Duplicate split row for canonical pair: {pair_id}")
        split = row["split"]
        if split not in {"train", "validation", "test"}:
            raise PreprocessingError(f"Invalid split {split!r} for {pair_id}")
        assignments[pair_id] = PairSplitAssignment(
            canonical_pair_id=pair_id,
            split=split,
            eligible_for_training=row["eligible_for_training"].lower() == "true",
            split_version=row["split_version"],
        )
    return assignments


def _resolve_project_path(project_root: Path, relative_path: str) -> Path:
    candidate = Path(relative_path)
    if candidate.is_absolute():
        raise PreprocessingError(f"Expected project-relative path, got {relative_path}")
    resolved = (project_root / candidate).resolve()
    root = project_root.resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise PreprocessingError(f"Path leaves project root: {relative_path}") from exc
    return resolved


def validate_mni152_training_record(
    record: CanonicalPairRecord,
    loaded_mri: np.ndarray,
    loaded_label: np.ndarray,
    affine: np.ndarray,
    label_affine: np.ndarray,
    spacing: tuple[float, float, float],
    orientation: tuple[str, str, str],
    assignments: Mapping[str, PairSplitAssignment],
) -> PairSplitAssignment:
    if record.space != EXPECTED_SPACE:
        raise PreprocessingError(f"Only MNI152 records are supported; got {record.space}")
    if record.pairing_status != "verified" or record.validation_status != "verified":
        raise PreprocessingError("Record is not verified")
    assignment = assignments.get(record.canonical_pair_id)
    if assignment is None:
        raise PreprocessingError(f"Missing split assignment for {record.canonical_pair_id}")
    if assignment.split_version != SPLIT_VERSION:
        raise PreprocessingError(f"Unexpected split version: {assignment.split_version}")
    if not assignment.eligible_for_training:
        raise PreprocessingError(f"Record is not eligible for MNI152 training: {record.canonical_pair_id}")
    if loaded_mri.shape != EXPECTED_SHAPE or loaded_label.shape != EXPECTED_SHAPE:
        raise PreprocessingError(f"Expected shape {EXPECTED_SHAPE}; got MRI {loaded_mri.shape}, label {loaded_label.shape}")
    if loaded_mri.shape != loaded_label.shape:
        raise PreprocessingError("MRI and label shapes do not match")
    if not np.allclose(spacing, EXPECTED_SPACING, rtol=AFFINE_RTOL, atol=AFFINE_ATOL):
        raise PreprocessingError(f"Expected spacing {EXPECTED_SPACING}; got {spacing}")
    if tuple(orientation) != EXPECTED_ORIENTATION:
        raise PreprocessingError(f"Expected LAS orientation; got {''.join(orientation)}")
    if not np.allclose(affine, label_affine, rtol=AFFINE_RTOL, atol=AFFINE_ATOL):
        raise PreprocessingError("MRI and label affines do not match")
    if not np.all(np.isfinite(loaded_mri)):
        raise PreprocessingError("MRI contains non-finite values")
    _validate_integer_labels(loaded_label)
    return assignment


def preprocess_verified_mni152_pair(
    project_root: Path,
    record: CanonicalPairRecord,
    *,
    dkt_dictionary_path: Path,
    class_mapping_path: Path,
    pair_splits_path: Path,
) -> PreprocessedPair:
    """Load one accepted MNI152 pair and return normalized arrays in memory."""
    assignments = load_pair_split_assignments(pair_splits_path)
    mapping = load_training_class_mapping(class_mapping_path)
    loaded = load_verified_pair(project_root, record, dkt_dictionary_path)
    assignment = validate_mni152_training_record(
        record=record,
        loaded_mri=loaded.mri,
        loaded_label=loaded.label,
        affine=loaded.affine,
        label_affine=loaded.label_affine,
        spacing=loaded.spacing,
        orientation=loaded.orientation,
        assignments=assignments,
    )
    contiguous = map_labels_to_training_classes(loaded.label, mapping)
    restored = inverse_map_training_classes(contiguous, mapping)
    if not np.array_equal(restored, loaded.label.astype(np.int16, copy=False)):
        raise PreprocessingError("Label mapping round trip failed")
    normalized, params = normalize_mri_per_volume(loaded.mri)
    mri_path = _resolve_project_path(project_root, record.mri_path)
    label_path = _resolve_project_path(project_root, record.label_path)
    return PreprocessedPair(
        normalized_mri=normalized,
        contiguous_label=contiguous,
        canonical_pair_id=record.canonical_pair_id,
        participant_group_id=record.participant_group_id,
        split=assignment.split,
        affine=np.asarray(loaded.affine, dtype=np.float64).copy(),
        original_shape=tuple(int(value) for value in loaded.mri.shape),
        original_spacing=tuple(float(value) for value in loaded.spacing),
        normalization=params,
        mapping_version=mapping.mapping_version,
        preprocessing_config_version=PREPROCESSING_CONFIG_VERSION,
        source_mri_path=record.mri_path,
        source_label_path=record.label_path,
        source_mri_sha256=sha256_file(mri_path),
        source_label_sha256=sha256_file(label_path),
    )
