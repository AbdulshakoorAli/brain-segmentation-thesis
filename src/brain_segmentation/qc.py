"""Deterministic NIfTI MRI/manual-label pair quality control."""

from __future__ import annotations

import hashlib
import re
from collections import defaultdict
from pathlib import Path
from typing import Iterable

import nibabel as nib
import numpy as np


AFFINE_RTOL = 1e-5
AFFINE_ATOL = 1e-5
BACKGROUND_VALUE = 0
REQUIRED_CHECK_COLUMNS = (
    "parse_status",
    "dimensions_status",
    "affine_status",
    "orientation_status",
    "spacing_status",
    "space_consistency_status",
    "mri_finite_status",
    "label_finite_status",
    "mri_nonempty_status",
    "mri_variation_status",
    "label_integer_status",
    "segmentation_nonempty_status",
    "label_vocabulary_status",
    "spatial_overlap_status",
    "duplicate_status",
)


def parse_dkt_cortical_definitions(path: Path) -> list[dict[str, str]]:
    """Parse only the distributed 62-row DKT cortical definition block."""
    text = path.read_text(encoding="utf-8")
    match = re.search(
        r"cortex_numbers_names\s*=\s*\[(.*?)\]\s*\n\s*#-+\s*\n"
        r"\s*# Noncortex label numbers and names",
        text,
        flags=re.DOTALL,
    )
    if not match:
        raise ValueError("Could not locate cortex_numbers_names in label definitions")
    entries = re.findall(r'\[\s*(\d+)\s*,\s*"([^"]+)"\s*\]', match.group(1))
    if len(entries) != 62:
        raise ValueError(f"Expected 62 cortical DKT definitions, found {len(entries)}")

    rows: list[dict[str, str]] = []
    seen: set[int] = set()
    for raw_id, raw_name in entries:
        label_id = int(raw_id)
        if label_id in seen:
            raise ValueError(f"Duplicate DKT label ID: {label_id}")
        seen.add(label_id)
        if raw_name.startswith("left "):
            hemisphere = "left"
            region_name = raw_name.removeprefix("left ")
        elif raw_name.startswith("right "):
            hemisphere = "right"
            region_name = raw_name.removeprefix("right ")
        else:
            raise ValueError(f"Cortical label lacks hemisphere prefix: {raw_name}")
        rows.append(
            {
                "original_label_id": str(label_id),
                "region_name": region_name,
                "hemisphere": hemisphere,
                "class_index": "",
                "source_reference": "data/raw/mindboggle101/metadata/label_definitions.txt:cortex_numbers_names",
            }
        )
    return rows


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def voxel_sha256(array: np.ndarray) -> str:
    """Hash decoded voxel values with shape and dtype, independent of NIfTI gzip bytes."""
    values = np.ascontiguousarray(array)
    digest = hashlib.sha256()
    digest.update(str(values.shape).encode("ascii"))
    digest.update(values.dtype.str.encode("ascii"))
    digest.update(values.tobytes(order="C"))
    return digest.hexdigest()


def _format_numbers(values: Iterable[float]) -> str:
    return ";".join(format(float(value), ".9g") for value in values)


def _format_shape(shape: tuple[int, ...]) -> str:
    return "x".join(str(value) for value in shape)


def _format_affine(affine: np.ndarray) -> str:
    return ";".join(format(float(value), ".12g") for value in affine.ravel(order="C"))


def _status(value: bool) -> str:
    return "passed" if value else "failed"


def _space_name_matches(path: Path, expected_space: str) -> bool:
    is_mni_name = ".MNI152.nii" in path.name
    if expected_space == "MNI152":
        return is_mni_name
    if expected_space == "native":
        return not is_mni_name
    return False


def evaluate_pair(
    mri_path: Path,
    label_path: Path,
    expected_space: str,
    known_label_ids: set[int],
) -> dict[str, str]:
    """Evaluate one same-space MRI/manual DKT pair without modifying either file."""
    result: dict[str, str] = {
        "mri_parse_status": "blocked",
        "label_parse_status": "blocked",
        "parse_status": "blocked",
    }
    try:
        mri_image = nib.load(str(mri_path))
        result["mri_parse_status"] = "passed"
    except Exception as exc:  # parser errors must be recorded, not hidden
        result["mri_parse_status"] = "failed"
        result["mri_parse_error"] = f"{type(exc).__name__}: {exc}"
        mri_image = None
    try:
        label_image = nib.load(str(label_path))
        result["label_parse_status"] = "passed"
    except Exception as exc:  # parser errors must be recorded, not hidden
        result["label_parse_status"] = "failed"
        result["label_parse_error"] = f"{type(exc).__name__}: {exc}"
        label_image = None

    result["parse_status"] = _status(mri_image is not None and label_image is not None)
    if mri_image is None or label_image is None:
        for column in REQUIRED_CHECK_COLUMNS:
            result.setdefault(column, "blocked")
        result["parse_status"] = "failed"
        return result

    mri_shape = tuple(int(value) for value in mri_image.shape)
    label_shape = tuple(int(value) for value in label_image.shape)
    result["mri_dimensions"] = _format_shape(mri_shape)
    result["label_dimensions"] = _format_shape(label_shape)
    dimensions_ok = len(mri_shape) == 3 and len(label_shape) == 3 and mri_shape == label_shape
    result["dimensions_status"] = _status(dimensions_ok)

    mri_affine = np.asarray(mri_image.affine, dtype=np.float64)
    label_affine = np.asarray(label_image.affine, dtype=np.float64)
    result["mri_affine"] = _format_affine(mri_affine)
    result["label_affine"] = _format_affine(label_affine)
    result["affine_rtol"] = format(AFFINE_RTOL, ".9g")
    result["affine_atol"] = format(AFFINE_ATOL, ".9g")
    result["affine_max_abs_difference"] = format(
        float(np.max(np.abs(mri_affine - label_affine))), ".12g"
    )
    affine_ok = bool(
        np.all(np.isfinite(mri_affine))
        and np.all(np.isfinite(label_affine))
        and np.allclose(mri_affine, label_affine, rtol=AFFINE_RTOL, atol=AFFINE_ATOL)
    )
    result["affine_status"] = _status(affine_ok)

    mri_orientation = "".join(nib.aff2axcodes(mri_affine))
    label_orientation = "".join(nib.aff2axcodes(label_affine))
    result["mri_orientation"] = mri_orientation
    result["label_orientation"] = label_orientation
    result["orientation_status"] = _status(mri_orientation == label_orientation)

    mri_spacing = tuple(float(value) for value in mri_image.header.get_zooms()[:3])
    label_spacing = tuple(float(value) for value in label_image.header.get_zooms()[:3])
    result["mri_voxel_spacing"] = _format_numbers(mri_spacing)
    result["label_voxel_spacing"] = _format_numbers(label_spacing)
    spacing_ok = bool(
        len(mri_spacing) == 3
        and len(label_spacing) == 3
        and np.all(np.isfinite(mri_spacing))
        and np.all(np.isfinite(label_spacing))
        and np.all(np.asarray(mri_spacing) > 0)
        and np.all(np.asarray(label_spacing) > 0)
        and np.allclose(mri_spacing, label_spacing, rtol=AFFINE_RTOL, atol=AFFINE_ATOL)
    )
    result["spacing_status"] = _status(spacing_ok)
    space_ok = (
        expected_space in {"native", "MNI152"}
        and _space_name_matches(mri_path, expected_space)
        and _space_name_matches(label_path, expected_space)
        and dimensions_ok
        and affine_ok
        and mri_orientation == label_orientation
        and spacing_ok
    )
    result["space_consistency_status"] = _status(space_ok)

    try:
        mri_data = np.asanyarray(mri_image.dataobj)
        result["mri_voxel_read_status"] = "passed"
    except Exception as exc:
        result["mri_voxel_read_status"] = "failed"
        result["mri_voxel_read_error"] = f"{type(exc).__name__}: {exc}"
        mri_data = None
    try:
        label_data = np.asanyarray(label_image.dataobj)
        result["label_voxel_read_status"] = "passed"
    except Exception as exc:
        result["label_voxel_read_status"] = "failed"
        result["label_voxel_read_error"] = f"{type(exc).__name__}: {exc}"
        label_data = None

    if mri_data is None or label_data is None:
        result["parse_status"] = "failed"
        for column in (
            "mri_finite_status",
            "label_finite_status",
            "mri_nonempty_status",
            "mri_variation_status",
            "label_integer_status",
            "segmentation_nonempty_status",
            "label_vocabulary_status",
            "spatial_overlap_status",
            "duplicate_status",
        ):
            result[column] = "blocked"
        return result

    mri_finite = bool(np.all(np.isfinite(mri_data)))
    label_finite = bool(np.all(np.isfinite(label_data)))
    result["mri_finite_status"] = _status(mri_finite)
    result["label_finite_status"] = _status(label_finite)

    finite_mri_values = mri_data[np.isfinite(mri_data)]
    if finite_mri_values.size:
        mri_min = float(np.min(finite_mri_values))
        mri_max = float(np.max(finite_mri_values))
        mri_nonzero_count = int(np.count_nonzero(finite_mri_values))
        result["mri_min"] = format(mri_min, ".12g")
        result["mri_max"] = format(mri_max, ".12g")
        result["mri_nonzero_voxel_count"] = str(mri_nonzero_count)
        result["mri_nonempty_status"] = _status(mri_nonzero_count > 0)
        result["mri_variation_status"] = _status(mri_max > mri_min)
    else:
        result["mri_nonempty_status"] = "failed"
        result["mri_variation_status"] = "failed"

    label_integer = bool(label_finite and np.all(label_data == np.rint(label_data)))
    result["label_integer_status"] = _status(label_integer)
    if label_integer:
        label_ids = sorted(int(value) for value in np.unique(label_data))
        anatomical_ids = [value for value in label_ids if value != BACKGROUND_VALUE]
        unknown_ids = sorted(set(anatomical_ids) - known_label_ids)
        result["label_ids"] = ";".join(str(value) for value in label_ids)
        result["anatomical_label_ids"] = ";".join(str(value) for value in anatomical_ids)
        result["unknown_label_ids"] = ";".join(str(value) for value in unknown_ids)
        result["label_vocabulary_status"] = _status(not unknown_ids)
    else:
        result["label_vocabulary_status"] = "blocked"

    foreground = np.isfinite(label_data) & (label_data != BACKGROUND_VALUE)
    segmentation_count = int(np.count_nonzero(foreground))
    result["segmentation_voxel_count"] = str(segmentation_count)
    result["segmentation_nonempty_status"] = _status(segmentation_count > 0)
    if dimensions_ok and mri_data.shape == label_data.shape:
        brain_support = np.isfinite(mri_data) & (mri_data != 0)
        overlap_count = int(np.count_nonzero(foreground & brain_support))
        result["mri_support_voxel_count"] = str(int(np.count_nonzero(brain_support)))
        result["overlap_voxel_count"] = str(overlap_count)
        result["segmentation_overlap_fraction"] = (
            format(overlap_count / segmentation_count, ".12g") if segmentation_count else ""
        )
        result["spatial_overlap_status"] = _status(segmentation_count > 0 and overlap_count > 0)
    else:
        result["spatial_overlap_status"] = "blocked"

    result["mri_file_sha256"] = sha256_file(mri_path)
    result["label_file_sha256"] = sha256_file(label_path)
    result["mri_voxel_sha256"] = voxel_sha256(mri_data)
    result["label_voxel_sha256"] = voxel_sha256(label_data)
    result["duplicate_status"] = "passed"
    return result


def annotate_duplicates(rows: list[dict[str, str]]) -> None:
    """Annotate exact compressed-file, decoded-voxel, and whole-pair duplicates."""
    keys = (
        "mri_file_sha256",
        "label_file_sha256",
        "mri_voxel_sha256",
        "label_voxel_sha256",
    )
    duplicate_fields = {
        "mri_file_sha256": "mri_exact_file_duplicate_scan_ids",
        "label_file_sha256": "label_exact_file_duplicate_scan_ids",
        "mri_voxel_sha256": "mri_exact_voxel_duplicate_scan_ids",
        "label_voxel_sha256": "label_exact_voxel_duplicate_scan_ids",
    }
    lookups: dict[str, dict[str, list[str]]] = {}
    for key in keys:
        groups: dict[str, list[str]] = defaultdict(list)
        for row in rows:
            if row.get(key):
                groups[row[key]].append(row["scan_id"])
        lookups[key] = groups
    pair_groups: dict[tuple[str, str], list[str]] = defaultdict(list)
    for row in rows:
        pair_key = (row.get("mri_voxel_sha256", ""), row.get("label_voxel_sha256", ""))
        if all(pair_key):
            pair_groups[pair_key].append(row["scan_id"])

    for row in rows:
        for key, output_field in duplicate_fields.items():
            matches = [item for item in lookups[key].get(row.get(key, ""), []) if item != row["scan_id"]]
            row[output_field] = ";".join(sorted(matches))
        pair_key = (row.get("mri_voxel_sha256", ""), row.get("label_voxel_sha256", ""))
        pair_matches = [item for item in pair_groups.get(pair_key, []) if item != row["scan_id"]]
        row["exact_pair_voxel_duplicate_scan_ids"] = ";".join(sorted(pair_matches))


def finalize_status(row: dict[str, str]) -> None:
    failed = [column for column in REQUIRED_CHECK_COLUMNS if row.get(column) == "failed"]
    blocked = [column for column in REQUIRED_CHECK_COLUMNS if row.get(column) == "blocked"]
    row["failed_checks"] = ";".join(failed)
    row["blocked_checks"] = ";".join(blocked)
    if failed:
        row["validation_status"] = "failed"
    elif blocked:
        row["validation_status"] = "blocked"
    else:
        row["validation_status"] = "verified"
