"""Minimal read-only loading for verified Mindboggle MRI/manual-DKT31 pairs."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

import nibabel as nib
import numpy as np

from brain_segmentation.qc import AFFINE_ATOL, AFFINE_RTOL, BACKGROUND_VALUE


@dataclass(frozen=True)
class CanonicalPairRecord:
    canonical_pair_id: str
    scan_id: str
    participant_id: str
    participant_group_id: str
    source_subject_id: str
    source_participant_identifier: str
    cohort: str
    mri_path: str
    label_path: str
    space: str
    mri_dimensions: str
    label_dimensions: str
    mri_voxel_spacing: str
    label_voxel_spacing: str
    mri_orientation: str
    label_orientation: str
    affine_match: str
    label_ids_present: str
    pairing_status: str
    validation_status: str

    @classmethod
    def from_row(cls, row: dict[str, str]) -> "CanonicalPairRecord":
        return cls(**{field: row[field] for field in cls.__dataclass_fields__})


@dataclass(frozen=True)
class LoadedCanonicalPair:
    record: CanonicalPairRecord
    mri: np.ndarray
    label: np.ndarray
    affine: np.ndarray
    label_affine: np.ndarray
    spacing: tuple[float, float, float]
    orientation: tuple[str, str, str]
    label_names: dict[int, str]
    observed_label_ids: tuple[int, ...]
    validation: dict[str, str]


def select_verified_record(
    manifest_path: Path,
    *,
    cohort: str,
    space: str,
) -> CanonicalPairRecord:
    """Select the first eligible row by canonical-pair ID then scan ID."""
    candidates = [
        record
        for record in load_verified_records(manifest_path)
        if record.cohort == cohort and record.space == space
    ]
    if not candidates:
        raise ValueError(f"No verified, included {cohort} {space} record exists")
    return min(candidates, key=lambda record: (record.canonical_pair_id, record.scan_id))


def load_verified_records(manifest_path: Path) -> tuple[CanonicalPairRecord, ...]:
    """Read all verified, non-excluded canonical pairs in stable order."""
    with manifest_path.open(newline="", encoding="utf-8-sig") as stream:
        rows = list(csv.DictReader(stream))
    eligible = [
        CanonicalPairRecord.from_row(row)
        for row in rows
        if row["pairing_status"] == "verified"
        and row["validation_status"] == "verified"
        and not row["exclusion_reason"]
    ]
    identifiers = [record.canonical_pair_id for record in eligible]
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("Manifest contains duplicate canonical_pair_id values")
    return tuple(sorted(eligible, key=lambda record: (record.cohort, record.participant_id, record.space, record.canonical_pair_id)))


def get_record_by_canonical_pair_id(
    records: tuple[CanonicalPairRecord, ...], canonical_pair_id: str
) -> CanonicalPairRecord:
    """Resolve one verified manifest record by its canonical identity."""
    matches = [record for record in records if record.canonical_pair_id == canonical_pair_id]
    if len(matches) != 1:
        raise ValueError(
            f"Expected one verified record for canonical_pair_id={canonical_pair_id!r}; found {len(matches)}"
        )
    return matches[0]


def load_dkt_dictionary(path: Path) -> dict[int, str]:
    """Load original DKT IDs without remapping them."""
    with path.open(newline="", encoding="utf-8-sig") as stream:
        rows = list(csv.DictReader(stream))
    labels: dict[int, str] = {}
    for row in rows:
        label_id = int(row["original_label_id"])
        if label_id in labels:
            raise ValueError(f"Duplicate DKT dictionary ID: {label_id}")
        labels[label_id] = f"{row['hemisphere']} {row['region_name']}"
    if not labels:
        raise ValueError("DKT dictionary is empty")
    return labels


def _resolve_project_path(project_root: Path, relative_path: str) -> Path:
    candidate = Path(relative_path)
    if candidate.is_absolute():
        raise ValueError(f"Manifest path must be relative: {relative_path}")
    root = project_root.resolve()
    resolved = (root / candidate).resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"Manifest path leaves project root: {relative_path}") from exc
    return resolved


def _parse_shape(value: str) -> tuple[int, int, int]:
    parsed = tuple(int(item) for item in value.split("x"))
    if len(parsed) != 3:
        raise ValueError(f"Expected 3D manifest shape, got {value}")
    return parsed


def _parse_spacing(value: str) -> tuple[float, float, float]:
    parsed = tuple(float(item) for item in value.split(";"))
    if len(parsed) != 3:
        raise ValueError(f"Expected three spacing values, got {value}")
    return parsed


def _pass(condition: bool, message: str) -> str:
    if not condition:
        raise ValueError(message)
    return "passed"


def load_verified_pair(
    project_root: Path,
    record: CanonicalPairRecord,
    dictionary_path: Path,
) -> LoadedCanonicalPair:
    """Load and validate one pair without transforms or source-file writes."""
    checks: dict[str, str] = {}
    checks["accepted_manifest_status"] = _pass(
        record.pairing_status == "verified" and record.validation_status == "verified",
        "Manifest record is not verified",
    )
    checks["supported_space"] = _pass(
        record.space in {"native", "MNI152"}, f"Unsupported coordinate space: {record.space}"
    )
    checks["manifest_affine_status"] = _pass(record.affine_match == "passed", "Manifest affine status is not passed")

    mri_path = _resolve_project_path(project_root, record.mri_path)
    label_path = _resolve_project_path(project_root, record.label_path)
    checks["files_exist"] = _pass(mri_path.is_file() and label_path.is_file(), "MRI or label file is missing")
    checks["same_subject"] = _pass(
        mri_path.parent == label_path.parent
        and record.participant_id in mri_path.parts
        and record.participant_id in label_path.parts,
        "MRI and label paths do not identify the same manifest subject",
    )
    mri_is_mni = ".MNI152.nii" in mri_path.name
    label_is_mni = ".MNI152.nii" in label_path.name
    expected_mni = record.space == "MNI152"
    checks["path_space_consistency"] = _pass(
        mri_is_mni == expected_mni and label_is_mni == expected_mni,
        f"File naming is inconsistent with manifest space {record.space}",
    )

    try:
        mri_image = nib.load(str(mri_path))
        label_image = nib.load(str(label_path))
    except Exception as exc:
        raise ValueError(f"NIfTI parsing failed: {type(exc).__name__}: {exc}") from exc
    checks["nifti_parsing"] = "passed"

    mri_shape = tuple(int(value) for value in mri_image.shape)
    label_shape = tuple(int(value) for value in label_image.shape)
    checks["three_dimensional"] = _pass(len(mri_shape) == len(label_shape) == 3, "Volumes must be 3D")
    checks["shape_match"] = _pass(mri_shape == label_shape, "MRI and label shapes differ")
    checks["manifest_shape_match"] = _pass(
        mri_shape == _parse_shape(record.mri_dimensions)
        and label_shape == _parse_shape(record.label_dimensions),
        "Observed shape differs from the accepted manifest",
    )

    mri_affine = np.asarray(mri_image.affine, dtype=np.float64)
    label_affine = np.asarray(label_image.affine, dtype=np.float64)
    checks["finite_affines"] = _pass(
        bool(np.all(np.isfinite(mri_affine)) and np.all(np.isfinite(label_affine))),
        "Affine contains non-finite values",
    )
    checks["affine_match"] = _pass(
        bool(np.allclose(mri_affine, label_affine, rtol=AFFINE_RTOL, atol=AFFINE_ATOL)),
        "MRI and label affines differ beyond accepted QC tolerance",
    )

    mri_spacing = tuple(float(value) for value in mri_image.header.get_zooms()[:3])
    label_spacing = tuple(float(value) for value in label_image.header.get_zooms()[:3])
    checks["spacing_match"] = _pass(
        bool(np.allclose(mri_spacing, label_spacing, rtol=AFFINE_RTOL, atol=AFFINE_ATOL)),
        "MRI and label spacing differs",
    )
    checks["manifest_spacing_match"] = _pass(
        bool(
            np.allclose(mri_spacing, _parse_spacing(record.mri_voxel_spacing), rtol=AFFINE_RTOL, atol=AFFINE_ATOL)
            and np.allclose(label_spacing, _parse_spacing(record.label_voxel_spacing), rtol=AFFINE_RTOL, atol=AFFINE_ATOL)
        ),
        "Observed spacing differs from the accepted manifest",
    )
    mri_orientation = tuple(str(value) for value in nib.aff2axcodes(mri_affine))
    label_orientation = tuple(str(value) for value in nib.aff2axcodes(label_affine))
    checks["orientation_match"] = _pass(mri_orientation == label_orientation, "MRI and label orientations differ")
    checks["manifest_orientation_match"] = _pass(
        "".join(mri_orientation) == record.mri_orientation
        and "".join(label_orientation) == record.label_orientation,
        "Observed orientation differs from the accepted manifest",
    )

    mri = np.asanyarray(mri_image.dataobj)
    label = np.asanyarray(label_image.dataobj)
    checks["finite_mri"] = _pass(bool(np.all(np.isfinite(mri))), "MRI contains non-finite values")
    checks["finite_labels"] = _pass(bool(np.all(np.isfinite(label))), "Labels contain non-finite values")
    checks["mri_nonempty"] = _pass(bool(np.count_nonzero(mri)), "MRI is empty")
    checks["mri_nonconstant"] = _pass(float(np.max(mri)) > float(np.min(mri)), "MRI is constant")
    checks["integer_labels"] = _pass(bool(np.all(label == np.rint(label))), "Labels are not integer-valued")

    observed = tuple(int(value) for value in np.unique(label))
    checks["segmentation_nonempty"] = _pass(
        any(value != BACKGROUND_VALUE for value in observed), "Segmentation is empty"
    )
    label_names = load_dkt_dictionary(dictionary_path)
    unknown = sorted(set(observed) - {BACKGROUND_VALUE} - set(label_names))
    checks["known_label_ids"] = _pass(not unknown, f"Unknown observed label IDs: {unknown}")
    manifest_ids = tuple(int(value) for value in record.label_ids_present.split(";") if value)
    checks["manifest_label_ids_match"] = _pass(observed == manifest_ids, "Observed IDs differ from accepted manifest")

    # Prevent accidental in-memory edits; the NIfTI files are never opened for writing.
    mri.setflags(write=False)
    label.setflags(write=False)
    mri_affine.setflags(write=False)
    label_affine.setflags(write=False)
    return LoadedCanonicalPair(
        record=record,
        mri=mri,
        label=label,
        affine=mri_affine,
        label_affine=label_affine,
        spacing=mri_spacing,
        orientation=mri_orientation,
        label_names=label_names,
        observed_label_ids=observed,
        validation=checks,
    )
