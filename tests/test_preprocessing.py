from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from brain_segmentation.loading import CanonicalPairRecord  # noqa: E402
from brain_segmentation.preprocessing import (  # noqa: E402
    EXPECTED_ORIENTATION,
    EXPECTED_SHAPE,
    EXPECTED_SPACE,
    EXPECTED_SPACING,
    PreprocessingError,
    TrainingClassMapping,
    inverse_map_training_classes,
    map_labels_to_training_classes,
    normalize_mri_per_volume,
    validate_mni152_training_record,
)


def mapping() -> TrainingClassMapping:
    return TrainingClassMapping(
        original_to_class={0: 0, 1002: 1, 2002: 2},
        class_to_original={0: 0, 1: 1002, 2: 2002},
        class_names={0: "background background", 1: "left region", 2: "right region"},
        mapping_version="test",
        source_path="synthetic",
    )


def valid_mri() -> np.ndarray:
    mri = np.zeros((3, 3, 3), dtype=np.float64)
    mri[0, 0, :] = [1, 2, 100]
    mri[1, 1, :] = [4, 5, 6]
    return mri


def test_valid_normalization_preserves_background_and_float32():
    mri = valid_mri()
    original = mri.copy()
    normalized, params = normalize_mri_per_volume(mri)
    foreground = mri != 0
    assert normalized.dtype == np.float32
    assert np.all(normalized[~foreground] == 0)
    assert np.isclose(float(normalized[foreground].mean()), 0, atol=1e-6)
    assert np.isclose(float(normalized[foreground].std()), 1, atol=1e-6)
    assert params.foreground_voxel_count == int(np.count_nonzero(foreground))
    assert np.array_equal(mri, original)


def test_percentile_clipping_uses_nonzero_voxels_only():
    mri = valid_mri()
    _, params = normalize_mri_per_volume(mri)
    nonzero = mri[mri != 0]
    assert params.lower_clip_value == pytest.approx(np.percentile(nonzero, 0.5))
    assert params.upper_clip_value == pytest.approx(np.percentile(nonzero, 99.5))


def test_normalization_is_deterministic():
    mri = valid_mri()
    first, first_params = normalize_mri_per_volume(mri)
    second, second_params = normalize_mri_per_volume(mri)
    assert np.array_equal(first, second)
    assert first_params == second_params


@pytest.mark.parametrize(
    "mri,match",
    [
        (np.array([[[0.0, np.nan]]]), "non-finite"),
        (np.zeros((2, 2, 2)), "foreground is empty"),
        (np.ones((2, 2, 2)), "standard deviation"),
        (np.ones((2, 2)), "3D"),
    ],
)
def test_invalid_mri_rejections(mri, match):
    with pytest.raises(PreprocessingError, match=match):
        normalize_mri_per_volume(mri)


def test_valid_forward_label_mapping_and_round_trip():
    labels = np.array([[[0, 1002], [2002, 1002]]], dtype=np.int16)
    mapped = map_labels_to_training_classes(labels, mapping())
    assert mapped.dtype == np.uint8
    assert mapped.tolist() == [[[0, 1], [2, 1]]]
    restored = inverse_map_training_classes(mapped, mapping())
    assert np.array_equal(restored, labels)
    assert np.array_equal(labels, np.array([[[0, 1002], [2002, 1002]]], dtype=np.int16))


def test_non_integer_label_rejected():
    labels = np.array([[[0.0, 1002.5]]], dtype=np.float32)
    with pytest.raises(PreprocessingError, match="non-integer"):
        map_labels_to_training_classes(labels, mapping())


def test_unknown_original_label_id_rejected():
    labels = np.array([[[0, 9999]]], dtype=np.int16)
    with pytest.raises(PreprocessingError, match="Unknown original"):
        map_labels_to_training_classes(labels, mapping())


def test_unknown_contiguous_class_rejected():
    classes = np.array([[[0, 3]]], dtype=np.uint8)
    with pytest.raises(PreprocessingError, match="Unknown contiguous"):
        inverse_map_training_classes(classes, mapping())


def record(space=EXPECTED_SPACE, pairing_status="verified", validation_status="verified") -> CanonicalPairRecord:
    return CanonicalPairRecord(
        canonical_pair_id="pair",
        scan_id="scan",
        participant_id="subject",
        participant_group_id="group",
        source_subject_id="source",
        source_participant_identifier="source",
        cohort="cohort",
        mri_path="mri.nii.gz",
        label_path="label.nii.gz",
        space=space,
        mri_dimensions="182x218x182",
        label_dimensions="182x218x182",
        mri_voxel_spacing="1;1;1",
        label_voxel_spacing="1;1;1",
        mri_orientation="LAS",
        label_orientation="LAS",
        affine_match="passed",
        label_ids_present="0;1002",
        pairing_status=pairing_status,
        validation_status=validation_status,
    )


class Assignment:
    split = "train"
    eligible_for_training = True
    split_version = "phase1b-1.0-seed20260831-participant_group_id-approved-20260920"


def valid_validation_inputs():
    mri = np.ones(EXPECTED_SHAPE, dtype=np.float32)
    label = np.zeros(EXPECTED_SHAPE, dtype=np.uint8)
    affine = np.eye(4)
    return mri, label, affine


def validate(**overrides):
    mri, label, affine = valid_validation_inputs()
    rec = overrides.pop("record", record())
    assignments = overrides.pop("assignments", {"pair": Assignment()})
    return validate_mni152_training_record(
        rec,
        overrides.pop("mri", mri),
        overrides.pop("label", label),
        overrides.pop("affine", affine),
        overrides.pop("label_affine", affine.copy()),
        overrides.pop("spacing", EXPECTED_SPACING),
        overrides.pop("orientation", EXPECTED_ORIENTATION),
        assignments,
    )


def test_valid_record_validation_passes():
    assert validate().split == "train"


def test_shape_mismatch_rejected():
    with pytest.raises(PreprocessingError, match="Expected shape"):
        validate(label=np.zeros((2, 2, 2), dtype=np.uint8))


def test_affine_mismatch_rejected():
    label_affine = np.eye(4)
    label_affine[0, 3] = 0.1
    with pytest.raises(PreprocessingError, match="affines"):
        validate(label_affine=label_affine)


def test_native_space_rejected():
    with pytest.raises(PreprocessingError, match="Only MNI152"):
        validate(record=record(space="native"))


def test_unverified_or_excluded_record_rejected():
    with pytest.raises(PreprocessingError, match="not verified"):
        validate(record=record(validation_status="failed"))


def test_missing_split_rejected():
    with pytest.raises(PreprocessingError, match="Missing split"):
        validate(assignments={})


def test_ineligible_split_rejected():
    class BadAssignment:
        split = "train"
        eligible_for_training = False
        split_version = "phase1b-1.0-seed20260831-participant_group_id-approved-20260920"

    with pytest.raises(PreprocessingError, match="not eligible"):
        validate(assignments={"pair": BadAssignment()})
