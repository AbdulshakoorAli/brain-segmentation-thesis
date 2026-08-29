from __future__ import annotations

import sys
from pathlib import Path

import nibabel as nib
import numpy as np
import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from brain_segmentation.qc import evaluate_pair  # noqa: E402


KNOWN_LABELS = {1002}


def save_pair(tmp_path: Path, mri: np.ndarray, label: np.ndarray, label_affine=None):
    affine = np.eye(4)
    mri_path = tmp_path / "t1weighted_brain.nii.gz"
    label_path = tmp_path / "labels.DKT31.manual.nii.gz"
    nib.save(nib.Nifti1Image(mri, affine), mri_path)
    nib.save(nib.Nifti1Image(label, affine if label_affine is None else label_affine), label_path)
    return mri_path, label_path


def valid_arrays():
    mri = np.zeros((4, 4, 4), dtype=np.float32)
    mri[1:3, 1:3, 1:3] = np.arange(1, 9, dtype=np.float32).reshape((2, 2, 2))
    label = np.zeros((4, 4, 4), dtype=np.int16)
    label[1:3, 1:3, 1:3] = 1002
    return mri, label


def run(tmp_path: Path, mri: np.ndarray, label: np.ndarray, label_affine=None):
    paths = save_pair(tmp_path, mri, label, label_affine)
    return evaluate_pair(*paths, "native", KNOWN_LABELS)


def test_valid_input_passes_required_voxel_and_geometry_checks(tmp_path):
    result = run(tmp_path, *valid_arrays())
    assert result["parse_status"] == "passed"
    assert result["dimensions_status"] == "passed"
    assert result["affine_status"] == "passed"
    assert result["mri_finite_status"] == "passed"
    assert result["label_finite_status"] == "passed"
    assert result["mri_nonempty_status"] == "passed"
    assert result["mri_variation_status"] == "passed"
    assert result["label_integer_status"] == "passed"
    assert result["segmentation_nonempty_status"] == "passed"
    assert result["label_vocabulary_status"] == "passed"
    assert result["spatial_overlap_status"] == "passed"


def test_shape_mismatch_fails_and_blocks_overlap(tmp_path):
    mri, _ = valid_arrays()
    label = np.zeros((3, 4, 4), dtype=np.int16)
    label[1, 1, 1] = 1002
    result = run(tmp_path, mri, label)
    assert result["dimensions_status"] == "failed"
    assert result["spatial_overlap_status"] == "blocked"


def test_affine_mismatch_fails(tmp_path):
    mri, label = valid_arrays()
    affine = np.eye(4)
    affine[0, 3] = 0.01
    assert run(tmp_path, mri, label, affine)["affine_status"] == "failed"


@pytest.mark.parametrize("target", ["mri", "label"])
def test_non_finite_values_fail(tmp_path, target):
    mri, label = valid_arrays()
    if target == "mri":
        mri[0, 0, 0] = np.nan
    else:
        label = label.astype(np.float32)
        label[0, 0, 0] = np.inf
    result = run(tmp_path, mri, label)
    assert result[f"{target}_finite_status"] == "failed"


def test_non_integer_labels_fail(tmp_path):
    mri, label = valid_arrays()
    label = label.astype(np.float32)
    label[1, 1, 1] = 1002.5
    result = run(tmp_path, mri, label)
    assert result["label_integer_status"] == "failed"
    assert result["label_vocabulary_status"] == "blocked"


def test_empty_segmentation_fails(tmp_path):
    mri, label = valid_arrays()
    label.fill(0)
    result = run(tmp_path, mri, label)
    assert result["segmentation_nonempty_status"] == "failed"
    assert result["spatial_overlap_status"] == "failed"


def test_unknown_label_id_fails(tmp_path):
    mri, label = valid_arrays()
    label[1, 1, 1] = 9999
    result = run(tmp_path, mri, label)
    assert result["label_vocabulary_status"] == "failed"
    assert result["unknown_label_ids"] == "9999"
