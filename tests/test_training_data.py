from __future__ import annotations

import csv
import sys
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from brain_segmentation.preprocessing import PreprocessingError  # noqa: E402
from brain_segmentation.training_data import MindboggleTrainingDataset, TrainingDataError  # noqa: E402

SPLIT_VERSION = "phase1b-1.0-seed20260831-participant_group_id-approved-20260920"
MANIFEST_FIELDS = [
    "scan_id", "canonical_pair_id", "participant_id", "participant_group_id", "source_subject_id",
    "source_participant_identifier", "cohort", "mri_path", "label_path", "space", "mri_dimensions",
    "label_dimensions", "mri_voxel_spacing", "label_voxel_spacing", "mri_orientation", "label_orientation",
    "affine_match", "label_ids_present", "pairing_status", "validation_status", "exclusion_reason",
]
PAIR_SPLIT_FIELDS = [
    "split_version", "canonical_pair_id", "scan_id", "subject_id", "participant_group_id", "cohort",
    "space", "split", "eligible_for_training", "validation_status", "pairing_status", "exclusion_reason",
    "assignment_hash", "notes",
]


def manifest_row(pair_id, split="train", space="MNI152", validation="verified", pairing="verified", exclusion=""):
    subject = pair_id.split(":")[-1]
    return {
        "scan_id": f"scan-{pair_id}",
        "canonical_pair_id": pair_id,
        "participant_id": f"participant-{subject}",
        "participant_group_id": f"group-{subject}",
        "source_subject_id": f"source-{subject}",
        "source_participant_identifier": f"sourcep-{subject}",
        "cohort": "CohortA" if pair_id.endswith("1") else "CohortB",
        "mri_path": f"data/raw/{pair_id}/t1weighted_brain.nii.gz",
        "label_path": f"data/raw/{pair_id}/labels.DKT31.manual.nii.gz",
        "space": space,
        "mri_dimensions": "182x218x182",
        "label_dimensions": "182x218x182",
        "mri_voxel_spacing": "1;1;1",
        "label_voxel_spacing": "1;1;1",
        "mri_orientation": "LAS",
        "label_orientation": "LAS",
        "affine_match": "passed",
        "label_ids_present": "0;1002",
        "pairing_status": pairing,
        "validation_status": validation,
        "exclusion_reason": exclusion,
    }


def split_row(pair_id, split="train", space="MNI152", eligible="true", validation="verified", pairing="verified", exclusion=""):
    subject = pair_id.split(":")[-1]
    return {
        "split_version": SPLIT_VERSION,
        "canonical_pair_id": pair_id,
        "scan_id": f"scan-{pair_id}",
        "subject_id": f"subject-{subject}",
        "participant_group_id": f"group-{subject}",
        "cohort": "CohortA" if pair_id.endswith("1") else "CohortB",
        "space": space,
        "split": split,
        "eligible_for_training": eligible,
        "validation_status": validation,
        "pairing_status": pairing,
        "exclusion_reason": exclusion,
        "assignment_hash": f"hash-{pair_id}",
        "notes": "",
    }


def write_csv(path: Path, fields, rows):
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def fixture_files(tmp_path, manifest_rows=None, split_rows=None):
    if manifest_rows is None:
        manifest_rows = [manifest_row("pair1", "train"), manifest_row("pair2", "validation"), manifest_row("pair3", "test")]
    if split_rows is None:
        split_rows = [split_row("pair1", "train"), split_row("pair2", "validation"), split_row("pair3", "test")]
    manifest = tmp_path / "manifest.csv"
    splits = tmp_path / "splits.csv"
    write_csv(manifest, MANIFEST_FIELDS, manifest_rows)
    write_csv(splits, PAIR_SPLIT_FIELDS, split_rows)
    return manifest, splits


@dataclass
class FakePreprocessor:
    calls: list[str]

    def __call__(self, project_root, record, **kwargs):
        self.calls.append(record.canonical_pair_id)
        split = {"pair1": "train", "pair2": "validation", "pair3": "test"}.get(record.canonical_pair_id, "train")
        return SimpleNamespace(
            normalized_mri=np.zeros((2, 2, 2), dtype=np.float32),
            contiguous_label=np.zeros((2, 2, 2), dtype=np.uint8),
            canonical_pair_id=record.canonical_pair_id,
            participant_group_id=record.participant_group_id,
            split=split,
            affine=np.eye(4),
            original_shape=(182, 218, 182),
            original_spacing=(1.0, 1.0, 1.0),
            normalization={"synthetic": True},
            mapping_version="mapping",
            preprocessing_config_version="config",
            source_mri_path=record.mri_path,
            source_label_path=record.label_path,
            source_mri_sha256="mrihash",
            source_label_sha256="labelhash",
        )


def dataset(tmp_path, split="train", manifest_rows=None, split_rows=None, preprocessor=None, allow_test=False):
    manifest, splits = fixture_files(tmp_path, manifest_rows, split_rows)
    return MindboggleTrainingDataset(
        tmp_path,
        split,
        allow_frozen_test=allow_test,
        manifest_path=manifest,
        pair_splits_path=splits,
        dkt_dictionary_path=tmp_path / "dkt.csv",
        class_mapping_path=tmp_path / "mapping.csv",
        preprocess_func=preprocessor or FakePreprocessor([]),
    )


def test_correct_train_and_validation_construction(tmp_path):
    train = dataset(tmp_path, "train")
    validation = dataset(tmp_path, "validation")
    assert len(train) == 1
    assert len(validation) == 1
    assert train.metadata[0].canonical_pair_id == "pair1"
    assert validation.metadata[0].canonical_pair_id == "pair2"


def test_explicit_test_construction_and_rejected_default(tmp_path):
    with pytest.raises(TrainingDataError, match="allow_frozen_test"):
        dataset(tmp_path, "test")
    test = dataset(tmp_path, "test", allow_test=True)
    assert len(test) == 1
    assert test.metadata[0].canonical_pair_id == "pair3"


def test_expected_counts_using_synthetic_fixtures(tmp_path):
    manifest_rows = [manifest_row(f"pair{i}", "train") for i in range(3)] + [manifest_row("pairv", "validation")]
    split_rows = [split_row(f"pair{i}", "train") for i in range(3)] + [split_row("pairv", "validation")]
    assert len(dataset(tmp_path, "train", manifest_rows, split_rows)) == 3
    assert len(dataset(tmp_path, "validation", manifest_rows, split_rows)) == 1


def test_deterministic_ordering_and_csv_row_order_independence(tmp_path):
    manifest_rows = [manifest_row("pair2", "train"), manifest_row("pair1", "train")]
    split_rows = [split_row("pair2", "train"), split_row("pair1", "train")]
    first = dataset(tmp_path, "train", manifest_rows, split_rows)
    second = dataset(tmp_path, "train", list(reversed(manifest_rows)), list(reversed(split_rows)))
    assert [m.canonical_pair_id for m in first.metadata] == [m.canonical_pair_id for m in second.metadata]


def test_metadata_enumeration_without_voxel_loading(tmp_path):
    fake = FakePreprocessor([])
    ds = dataset(tmp_path, "train", preprocessor=fake)
    assert len(ds.metadata) == 1
    assert list(ds)[0].canonical_pair_id == "pair1"
    assert fake.calls == []


def test_lazy_single_record_loading_and_canonical_lookup(tmp_path):
    fake = FakePreprocessor([])
    ds = dataset(tmp_path, "train", preprocessor=fake)
    item = ds.load_item(0)
    assert item.canonical_pair_id == "pair1"
    assert item.normalized_mri.dtype == np.float32
    assert fake.calls == ["pair1"]
    assert ds.get_metadata_by_canonical_pair_id("pair1").canonical_pair_id == "pair1"


def test_unknown_and_cross_split_canonical_id_rejections(tmp_path):
    ds = dataset(tmp_path, "train")
    with pytest.raises(TrainingDataError, match="Unknown canonical"):
        ds.get_metadata_by_canonical_pair_id("missing")
    with pytest.raises(TrainingDataError, match="belongs to split"):
        ds.get_metadata_by_canonical_pair_id("pair2")


def test_native_row_exclusion_and_rejection(tmp_path):
    manifest_rows = [manifest_row("pair1", "train", space="MNI152"), manifest_row("native1", "train", space="native")]
    split_rows = [split_row("pair1", "train", space="MNI152"), split_row("native1", "train", space="native", eligible="false")]
    ds = dataset(tmp_path, "train", manifest_rows, split_rows)
    assert [m.canonical_pair_id for m in ds.metadata] == ["pair1"]
    with pytest.raises(TrainingDataError, match="not an MNI152"):
        ds.get_metadata_by_canonical_pair_id("native1")


def test_native_training_eligible_row_rejected(tmp_path):
    with pytest.raises(TrainingDataError, match="Native or non-MNI152"):
        dataset(tmp_path, "train", [manifest_row("native1", "train", space="native")], [split_row("native1", "train", space="native", eligible="true")])


@pytest.mark.parametrize(
    "manifest_kwargs,split_kwargs,match",
    [
        ({"validation": "failed"}, {"validation": "verified"}, "no verified manifest"),
        ({"exclusion": "exclude"}, {"exclusion": ""}, "no verified manifest"),
        ({}, {"eligible": "false"}, "not training-eligible"),
        ({}, {"validation": "failed"}, "Unverified record"),
        ({}, {"exclusion": "exclude"}, "Excluded record"),
    ],
)
def test_invalid_record_rejections(tmp_path, manifest_kwargs, split_kwargs, match):
    with pytest.raises(TrainingDataError, match=match):
        dataset(tmp_path, "train", [manifest_row("pair1", "train", **manifest_kwargs)], [split_row("pair1", "train", **split_kwargs)])


def test_duplicate_canonical_id_rejected(tmp_path):
    rows = [manifest_row("pair1", "train")]
    split_rows = [split_row("pair1", "train"), split_row("pair1", "train")]
    with pytest.raises(TrainingDataError, match="Duplicate canonical"):
        dataset(tmp_path, "train", rows, split_rows)


def test_missing_split_and_invalid_split_rejected(tmp_path):
    with pytest.raises(TrainingDataError, match="Missing split"):
        dataset(tmp_path, "train", [manifest_row("pair1", "train")], [])
    with pytest.raises(TrainingDataError, match="Unknown split"):
        dataset(tmp_path, "bad")
    with pytest.raises(TrainingDataError, match="Invalid split"):
        dataset(tmp_path, "train", [manifest_row("pair1", "train")], [split_row("pair1", "bad")])


def test_out_of_range_index_rejected(tmp_path):
    ds = dataset(tmp_path, "train")
    with pytest.raises(TrainingDataError, match="Index out of range"):
        ds.load_item(9)


def test_preprocessing_errors_propagate_clearly(tmp_path):
    def bad(*args, **kwargs):
        raise PreprocessingError("synthetic preprocessing failure")
    ds = dataset(tmp_path, "train", preprocessor=bad)
    with pytest.raises(PreprocessingError, match="synthetic preprocessing failure"):
        ds.load_item(0)


def test_input_metadata_is_not_modified(tmp_path):
    manifest_rows = [manifest_row("pair1", "train")]
    split_rows = [split_row("pair1", "train")]
    original_manifest = [row.copy() for row in manifest_rows]
    original_splits = [row.copy() for row in split_rows]
    ds = dataset(tmp_path, "train", manifest_rows, split_rows)
    _ = ds.summary()
    assert manifest_rows == original_manifest
    assert split_rows == original_splits

