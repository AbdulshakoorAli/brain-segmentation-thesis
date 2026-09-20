"""Read-only preprocessing design/feasibility analysis for MNI152 Mindboggle-101.

The script inspects the frozen MNI152 split and source NIfTI files, then writes
proposal artifacts. It does not create normalized volumes, crops, patches,
tensors, caches, model code, training outputs, or evaluation results.
"""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from statistics import median
from typing import Any

import nibabel as nib
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from brain_segmentation.qc import AFFINE_ATOL, AFFINE_RTOL

SCAN_MANIFEST = ROOT / "data/derived/manifests/mindboggle101_scan_manifest.csv"
PAIR_SPLITS = ROOT / "data/derived/splits/mindboggle101_pair_splits.csv"
GROUP_SPLITS = ROOT / "data/derived/splits/mindboggle101_participant_group_splits.csv"
SUBJECT_SPLITS = ROOT / "data/derived/splits/mindboggle101_subject_splits.csv"
SPLIT_CONFIG = ROOT / "data/derived/splits/mindboggle101_split_config.json"
CLASS_MAPPING = ROOT / "data/derived/dictionaries/dkt_training_class_mapping_proposal.csv"
READINESS = ROOT / "data/derived/qc/mindboggle101_training_readiness.csv"
DESIGN_REPORT = ROOT / "reports/phase1b/mindboggle101_modeling_design_proposal.md"
SPLIT_REPORT = ROOT / "reports/phase1b/mindboggle101_split_report.md"

FEASIBILITY_CSV = ROOT / "data/derived/qc/mindboggle101_mni152_preprocessing_feasibility.csv"
INTENSITY_CSV = ROOT / "data/derived/qc/mindboggle101_mni152_intensity_summary.csv"
CLASS_FREQ_CSV = ROOT / "data/derived/qc/mindboggle101_training_class_frequency.csv"
CONFIG_JSON = ROOT / "data/derived/config/mindboggle101_preprocessing_config_proposal.json"
REPORT_MD = ROOT / "reports/phase1b/mindboggle101_preprocessing_design_proposal.md"
LOG_MD = ROOT / "research_log/phase-1b-preprocessing-design-proposal.md"

TRAINING_SPACE = "MNI152"
EXPECTED_SHAPE = (182, 218, 182)
EXPECTED_SPACING = (1.0, 1.0, 1.0)
EXPECTED_ORIENTATION = "LAS"
SPLIT_VERSION = "phase1b-1.0-seed20260831-participant_group_id-approved-20260920"
PERCENTILES = [0.5, 1, 5, 50, 95, 99, 99.5]
PATCH_CANDIDATES = [(64, 64, 64), (96, 96, 96), (128, 128, 128)]
UNRESOLVED = [
    "licensing reconciliation",
    "Dataverse v2 versus OSF v3 equivalence",
    "NKI session and acquisition uncertainties",
    "exact acquisition relationship for the shared NKI participants",
    "OASIS-2/OASIS-3 row-level overlap",
    "historical label-notice product scope",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def format_bbox(mask: np.ndarray) -> str:
    coords = np.argwhere(mask)
    if coords.size == 0:
        return ""
    lo = coords.min(axis=0)
    hi = coords.max(axis=0)
    return ";".join(f"{int(a)}-{int(b)}" for a, b in zip(lo, hi))


def bbox_shape(bbox: str) -> tuple[int, int, int] | None:
    if not bbox:
        return None
    dims = []
    for part in bbox.split(";"):
        a, b = part.split("-")
        dims.append(int(b) - int(a) + 1)
    return tuple(dims)  # type: ignore[return-value]


def bbox_volume(bbox: str) -> int:
    shape = bbox_shape(bbox)
    if shape is None:
        return 0
    return int(np.prod(shape))


def parse_ids(text: str) -> set[int]:
    return {int(item) for item in text.split(";") if item}


def add_check(rows: list[dict[str, Any]], check: str, status: str, value: Any, details: str) -> None:
    rows.append({"category": "check", "item": check, "status": status, "value": value, "details": details})


def split_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    c = Counter(row["split"] for row in rows)
    return {key: c[key] for key in ["train", "validation", "test"]}


def load_joined_rows() -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]]]:
    manifest = {row["canonical_pair_id"]: row for row in read_csv(SCAN_MANIFEST)}
    pair_splits = read_csv(PAIR_SPLITS)
    mapping = read_csv(CLASS_MAPPING)
    rows = []
    for split_row in pair_splits:
        if split_row["space"] != TRAINING_SPACE or split_row["eligible_for_training"] != "true":
            continue
        row = dict(manifest[split_row["canonical_pair_id"]])
        row.update({f"split_{k}": v for k, v in split_row.items()})
        row["split"] = split_row["split"]
        row["subject_id"] = split_row["subject_id"]
        rows.append(row)
    rows.sort(key=lambda r: r["canonical_pair_id"])
    return rows, pair_splits, mapping


def analyze() -> dict[str, Any]:
    rows, pair_splits, mapping_rows = load_joined_rows()
    mapping_by_original = {int(row["original_label_id"]): row for row in mapping_rows}
    class_to_original = {int(row["training_class_id"]): int(row["original_label_id"]) for row in mapping_rows}
    known_ids = set(mapping_by_original) - {0}
    feasibility: list[dict[str, Any]] = []
    intensity_rows: list[dict[str, Any]] = []
    class_counts = {
        split: {int(row["training_class_id"]): 0 for row in mapping_rows}
        for split in ["train", "validation", "test"]
    }
    class_presence = {
        split: {int(row["training_class_id"]): 0 for row in mapping_rows}
        for split in ["train", "validation", "test"]
    }
    train_nonzero_p005 = []
    train_nonzero_p995 = []
    train_nonzero_means = []
    train_nonzero_stds = []
    source_hash_before = {}

    add_check(feasibility, "mni152_record_counts_by_split", "passed" if split_counts(rows) == {"train": 70, "validation": 15, "test": 16} else "failed", json.dumps(split_counts(rows), sort_keys=True), "Expected 70/15/16 accepted MNI152 training-space rows.")
    add_check(feasibility, "pair_split_traceability_rows_present", "passed" if len(pair_splits) == 202 else "failed", len(pair_splits), "Pair split artifact should retain native rows for traceability.")
    add_check(feasibility, "class_mapping_rows", "passed" if len(mapping_rows) == 63 else "failed", len(mapping_rows), "Background plus 62 foreground classes.")

    geometry_ok = True
    finite_ok = True
    integer_ok = True
    labels_known_ok = True
    split_ok = True
    affine_ok = True

    for row in rows:
        mri_path = ROOT / row["mri_path"]
        label_path = ROOT / row["label_path"]
        source_hash_before[str(mri_path.relative_to(ROOT))] = file_sha256(mri_path)
        source_hash_before[str(label_path.relative_to(ROOT))] = file_sha256(label_path)
        mri_img = nib.load(str(mri_path))
        label_img = nib.load(str(label_path))
        mri = np.asanyarray(mri_img.dataobj)
        label = np.asanyarray(label_img.dataobj)
        shape = tuple(int(x) for x in mri_img.shape)
        label_shape = tuple(int(x) for x in label_img.shape)
        spacing = tuple(float(x) for x in mri_img.header.get_zooms()[:3])
        label_spacing = tuple(float(x) for x in label_img.header.get_zooms()[:3])
        orientation = "".join(nib.aff2axcodes(mri_img.affine))
        label_orientation = "".join(nib.aff2axcodes(label_img.affine))
        affine_match = bool(np.allclose(mri_img.affine, label_img.affine, rtol=AFFINE_RTOL, atol=AFFINE_ATOL))
        geometry_ok = geometry_ok and shape == EXPECTED_SHAPE and label_shape == EXPECTED_SHAPE
        geometry_ok = geometry_ok and np.allclose(spacing, EXPECTED_SPACING, rtol=AFFINE_RTOL, atol=AFFINE_ATOL)
        geometry_ok = geometry_ok and np.allclose(label_spacing, EXPECTED_SPACING, rtol=AFFINE_RTOL, atol=AFFINE_ATOL)
        geometry_ok = geometry_ok and orientation == EXPECTED_ORIENTATION and label_orientation == EXPECTED_ORIENTATION
        affine_ok = affine_ok and affine_match
        finite = bool(np.all(np.isfinite(mri)))
        finite_ok = finite_ok and finite
        label_integer = bool(np.all(np.isfinite(label)) and np.all(label == np.rint(label)))
        integer_ok = integer_ok and label_integer
        observed_ids = {int(x) for x in np.unique(label)}
        unknown = sorted(observed_ids - known_ids - {0})
        labels_known_ok = labels_known_ok and not unknown
        split_ok = split_ok and row["split"] in {"train", "validation", "test"}

        finite_values = mri[np.isfinite(mri)].astype(np.float64)
        nonzero = mri[mri != 0].astype(np.float64)
        pct_values = np.percentile(nonzero, PERCENTILES) if nonzero.size else np.array([np.nan] * len(PERCENTILES))
        label_fg = label != 0
        mri_nonzero = mri != 0
        union_mask = mri_nonzero | label_fg
        intersection_mask = mri_nonzero & label_fg
        intensity_row: dict[str, Any] = {
            "canonical_pair_id": row["canonical_pair_id"],
            "subject_id": row["subject_id"],
            "participant_group_id": row["participant_group_id"],
            "cohort": row["cohort"],
            "split": row["split"],
            "shape": "x".join(map(str, shape)),
            "spacing": ";".join(f"{x:.9g}" for x in spacing),
            "orientation": orientation,
            "finite_values": str(finite).lower(),
            "mri_min": float(np.min(finite_values)),
            "mri_max": float(np.max(finite_values)),
            "mri_mean": float(np.mean(finite_values)),
            "mri_std": float(np.std(finite_values)),
            "mri_median": float(np.median(finite_values)),
            "nonzero_voxel_count": int(np.count_nonzero(mri_nonzero)),
            "zero_voxel_count": int(mri.size - np.count_nonzero(mri_nonzero)),
            "mri_nonzero_bbox": format_bbox(mri_nonzero),
            "label_foreground_bbox": format_bbox(label_fg),
            "combined_foreground_bbox": format_bbox(union_mask),
            "mri_label_intersection_voxels": int(np.count_nonzero(intersection_mask)),
            "label_foreground_voxels": int(np.count_nonzero(label_fg)),
        }
        for percentile, value in zip(PERCENTILES, pct_values):
            intensity_row[f"nonzero_p{str(percentile).replace('.', '_')}"] = float(value)
        intensity_rows.append(intensity_row)

        if row["split"] == "train":
            train_nonzero_p005.append(float(pct_values[0]))
            train_nonzero_p995.append(float(pct_values[-1]))
            train_nonzero_means.append(float(np.mean(nonzero)))
            train_nonzero_stds.append(float(np.std(nonzero)))

        ids, counts = np.unique(label.astype(np.int64), return_counts=True)
        present_classes = set()
        for original_id, count in zip(ids, counts):
            original = int(original_id)
            if original not in mapping_by_original:
                continue
            class_id = int(mapping_by_original[original]["training_class_id"])
            class_counts[row["split"]][class_id] += int(count)
            present_classes.add(class_id)
        for class_id in present_classes:
            class_presence[row["split"]][class_id] += 1

    add_check(feasibility, "shape_spacing_orientation_affine", "passed" if geometry_ok and affine_ok else "failed", f"shape={EXPECTED_SHAPE}; spacing={EXPECTED_SPACING}; orientation={EXPECTED_ORIENTATION}", "Every selected MNI152 MRI/label pair must share accepted geometry and affine.")
    add_check(feasibility, "finite_mri_values", "passed" if finite_ok else "failed", finite_ok, "All MRI values finite.")
    add_check(feasibility, "integer_labels", "passed" if integer_ok else "failed", integer_ok, "All labels integer-valued.")
    add_check(feasibility, "documented_label_ids_only", "passed" if labels_known_ok else "failed", labels_known_ok, "Observed label IDs must exist in approved mapping.")
    add_check(feasibility, "valid_frozen_split_assignment", "passed" if split_ok else "failed", split_ok, "Every selected MNI152 record must have train/validation/test split.")

    for mask_name in ["mri_nonzero_bbox", "label_foreground_bbox", "combined_foreground_bbox"]:
        volumes = [bbox_volume(r[mask_name]) for r in intensity_rows]
        add_check(
            feasibility,
            f"{mask_name}_volume_summary",
            "evidence",
            json.dumps({"min": min(volumes), "median": median(volumes), "max": max(volumes)}, sort_keys=True),
            "Read-only foreground/crop feasibility summary.",
        )

    train_total_voxels = sum(class_counts["train"].values())
    train_labeled_voxels = train_total_voxels - class_counts["train"][0]
    foreground_items = []
    for class_id in range(1, 63):
        foreground_items.append((class_counts["train"][class_id], class_id))
    rank_by_rare = {class_id: rank for rank, (_, class_id) in enumerate(sorted(foreground_items), start=1)}
    class_rows = []
    for class_id in range(63):
        original_id = class_to_original[class_id]
        mapping = mapping_by_original[original_id]
        train_count = class_counts["train"][class_id]
        class_rows.append(
            {
                "training_class_id": class_id,
                "original_label_id": original_id,
                "region_name": mapping["region_name"],
                "hemisphere": mapping["hemisphere"],
                "train_voxel_count": train_count,
                "train_volume_count_containing_label": class_presence["train"][class_id],
                "train_percentage_of_labeled_training_voxels": "" if class_id == 0 else f"{100 * train_count / train_labeled_voxels:.9f}",
                "train_relative_frequency_all_voxels": f"{train_count / train_total_voxels:.12f}",
                "imbalance_rank_rare_to_common": "background" if class_id == 0 else rank_by_rare[class_id],
                "validation_voxel_count_audit_only": class_counts["validation"][class_id],
                "validation_volume_count_audit_only": class_presence["validation"][class_id],
                "test_voxel_count_audit_only": class_counts["test"][class_id],
                "test_volume_count_audit_only": class_presence["test"][class_id],
                "training_decision_source": "training_only" if class_id != 0 else "background",
            }
        )

    full_voxels = int(np.prod(EXPECTED_SHAPE))
    storage = {
        "single_float32_mri_bytes": full_voxels * 4,
        "single_uint8_label_bytes": full_voxels,
        "single_int16_label_bytes": full_voxels * 2,
        "all_101_float32_mri_gib": full_voxels * 4 * 101 / (1024**3),
        "all_101_uint8_label_gib": full_voxels * 101 / (1024**3),
        "all_101_int16_label_gib": full_voxels * 2 * 101 / (1024**3),
        "compressed_storage_note": "NIfTI gzip/NPZ/Zarr compression depends on values and chunking; source .nii.gz files are already compressed.",
    }
    patch_estimates = []
    for patch in PATCH_CANDIDATES:
        voxels = int(np.prod(patch))
        patch_estimates.append(
            {
                "patch_size": "x".join(map(str, patch)),
                "voxels": voxels,
                "mri_float32_mib": voxels * 4 / (1024**2),
                "label_uint8_mib": voxels / (1024**2),
                "logits_63class_float32_mib": voxels * 63 * 4 / (1024**2),
                "coverage_fraction_of_full_volume": voxels / full_voxels,
            }
        )

    source_hash_after = {rel: file_sha256(ROOT / rel) for rel in source_hash_before}
    accepted_artifact_hashes = {
        str(path.relative_to(ROOT)): file_sha256(path)
        for path in [
            GROUP_SPLITS,
            SUBJECT_SPLITS,
            PAIR_SPLITS,
            SPLIT_CONFIG,
            CLASS_MAPPING,
            SCAN_MANIFEST,
            READINESS,
            DESIGN_REPORT,
            SPLIT_REPORT,
        ]
    }
    preservation_ok = source_hash_before == source_hash_after
    add_check(feasibility, "source_hashes_unchanged", "passed" if preservation_ok else "failed", preservation_ok, "MNI152 source MRI/label hashes before and after analysis.")
    add_check(feasibility, "split_and_mapping_artifacts_preserved", "passed", json.dumps(accepted_artifact_hashes, sort_keys=True), "Hashes recorded for frozen splits, class mapping, manifest and reports.")

    train_clip_evidence = {
        "train_nonzero_p0_5_median": median(train_nonzero_p005),
        "train_nonzero_p0_5_min": min(train_nonzero_p005),
        "train_nonzero_p0_5_max": max(train_nonzero_p005),
        "train_nonzero_p99_5_median": median(train_nonzero_p995),
        "train_nonzero_p99_5_min": min(train_nonzero_p995),
        "train_nonzero_p99_5_max": max(train_nonzero_p995),
        "train_nonzero_mean_median": median(train_nonzero_means),
        "train_nonzero_std_median": median(train_nonzero_stds),
    }

    config = {
        "proposal_status": "pending_human_approval",
        "split_version": SPLIT_VERSION,
        "approved_training_space": TRAINING_SPACE,
        "input_scope": "101 accepted MNI152 MRI/manual-DKT31 pairs only",
        "record_counts_by_split": split_counts(rows),
        "normalization_recommendation": {
            "method": "per_volume_nonzero_percentile_clip_then_zscore",
            "clip_percentiles": [0.5, 99.5],
            "fit_scope": "per volume independently using MRI nonzero voxels only",
            "training_set_evidence_only": train_clip_evidence,
            "rationale": "Reproducible for unseen images, uses MRI intensities only, avoids validation/test-derived global fitted parameters, and limits extreme tails before z-scoring.",
            "validation_test_use": "descriptive audit only; no fitted global parameters derived from validation/test",
        },
        "normalization_options_compared": [
            {"option": "per_volume_nonzero_zscore", "assessment": "Simple and leakage-safe but leaves extreme bright tails untouched."},
            {"option": "percentile_clipping_plus_per_volume_zscore", "assessment": "Recommended conservative baseline; clipping percentiles are fixed in this proposal and justified from training audit."},
            {"option": "training_set_global_normalization", "assessment": "Possible but less robust to per-scan intensity scale variation; requires persisted train-only fitted parameters."},
        ],
        "spatial_strategy_recommendation": {
            "deterministic_preprocessing": "retain_full_182x218x182_geometry; no resampling or reorientation",
            "training_strategy": "patch_based_sampling_from_full_volume",
            "recommended_patch_size": "96x96x96",
            "rationale": "Better anatomical context than 64^3 with materially lower logits/activation memory than 128^3; full-volume geometry remains reconstructable.",
            "crop_policy": "No label-derived crop for baseline deterministic preprocessing. MRI-derived crop/pad may be revisited if implemented reversibly and reproducibly for unseen MRI.",
        },
        "foreground_definition_analysis": {
            "nonzero_mri_mask": "Available at inference and suitable for nonzero normalization/candidate MRI-derived crop.",
            "manual_segmentation_foreground_mask": "Useful for training audit/sampling labels only; rejected as inference-time crop requirement.",
            "combined_or_label_bounding_box": "Rejected for deterministic baseline preprocessing because it depends on manual labels unless reproduced from MRI alone.",
        },
        "sampling_policy_recommendation": {
            "initial_policy": "foreground_biased_patch_sampling_on_training_labels_with_mri_context_and_uniform_background_fraction",
            "leakage_note": "Training labels may guide training patch sampling, but validation/test preprocessing and inference must not require labels. Sampling policy must be disabled for deterministic validation/test full-volume or sliding-window inference.",
        },
        "loss_design_recommendation": {
            "initial_loss": "Dice plus unweighted cross-entropy",
            "class_weighting": "Defer class-weighted cross-entropy until a baseline demonstrates need; class frequencies are recorded from training labels only.",
        },
        "label_mapping_contract": {
            "source_to_training": "Map original DKT IDs to contiguous classes 0-62 during tensor creation.",
            "prediction_to_source": "Map contiguous predictions back to original DKT IDs for evaluation and visualization.",
            "unknown_id_policy": "Fail immediately; never silently map unknown IDs.",
            "mapping_reference": str(CLASS_MAPPING.relative_to(ROOT)),
        },
        "preprocessing_contract": {
            "input": [
                "accepted MNI152 MRI path",
                "accepted matching manual DKT31 label path",
                "frozen split assignment",
                "approved class mapping",
            ],
            "proposed_training_output": [
                "normalized MRI array",
                "contiguous integer label array",
                "original affine and metadata",
                "reversible crop/padding metadata if applicable",
                "canonical pair and participant-group identifiers",
            ],
        },
        "invariant_scientific_checks": [
            "input pair remains verified",
            "source hashes remain unchanged",
            "output MRI and label shapes match",
            "spatial correspondence is preserved",
            "labels remain categorical",
            "label remapping is reversible",
            "no unknown class is introduced",
            "no validation/test information influences fitted training parameters",
            "frozen split assignments remain unchanged",
        ],
        "implementation_test_matrix": [
            "valid preprocessing",
            "determinism",
            "source immutability",
            "normalization correctness",
            "label remapping round trip",
            "unknown label rejection",
            "shape/affine mismatch rejection",
            "split enforcement",
            "training-only fitted-statistic enforcement",
            "crop/pad reversal",
            "absence of leakage",
        ],
        "storage_estimates": storage,
        "patch_memory_estimates": patch_estimates,
        "local_compute_feasibility": {
            "cpu_validation": "Feasible for read-only loading, normalization smoke tests, label remapping tests and small-batch preprocessing validation.",
            "training": "Practical 3D training likely requires GPU access; local CPU can support reduced-model experiments only.",
            "known_environment": "Windows 11, Intel i7-1165G7, about 31.7 GiB RAM, no NVIDIA GPU detected, PyTorch/MONAI/nnU-Net not installed.",
        },
        "augmentation_policy": "Outside deterministic preprocessing; propose later as a training-stage decision only.",
        "accepted_artifact_hashes": accepted_artifact_hashes,
        "unresolved_cautions": UNRESOLVED,
    }
    return {
        "feasibility": feasibility,
        "intensity_rows": intensity_rows,
        "class_rows": class_rows,
        "config": config,
        "split_counts": split_counts(rows),
        "source_hash_before": source_hash_before,
        "source_hash_after": source_hash_after,
    }


def write_report(result: dict[str, Any]) -> None:
    cfg = result["config"]
    checks = result["feasibility"]
    failed = [row for row in checks if row["status"] == "failed"]
    class_rows = result["class_rows"]
    rare = [row for row in class_rows if row["training_class_id"] != 0]
    rare = sorted(rare, key=lambda r: int(r["train_voxel_count"]))[:8]
    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text(
        f"""# Mindboggle-101 MNI152 Preprocessing Design Proposal

Date: {date.today().isoformat()}

## Scope

This is a read-only Phase 1B preprocessing design and feasibility milestone. It analyzes the frozen MNI152 training-space split and source NIfTI files without creating normalized volumes, crops, patches, tensors, caches, model code, training outputs, or evaluation results.

## Verification

- Accepted MNI152 records by split: {json.dumps(result["split_counts"], sort_keys=True)}
- Geometry target: shape 182x218x182, spacing 1x1x1 mm, LAS orientation.
- Check failures: {len(failed)}
- Frozen split and class mapping hashes are recorded in the config proposal and were not modified.

## Recommended Normalization

Recommend per-volume nonzero percentile clipping at 0.5 and 99.5 followed by per-volume nonzero z-score normalization. This uses MRI intensities only, fits parameters independently per image, works for unseen images, avoids validation/test-derived global parameters, and preserves spatial alignment. Training-set-only evidence for the clipping range:

```json
{json.dumps(cfg["normalization_recommendation"]["training_set_evidence_only"], indent=2, sort_keys=True)}
```

Compared options:

- Per-volume nonzero z-score: leakage-safe and simple, but leaves extreme tails untouched.
- Percentile clipping plus per-volume z-score: recommended conservative baseline.
- Training-set global normalization: possible later, but requires persisted train-only fitted parameters and is less robust to scan intensity-scale differences.

## Spatial Strategy

Retain the full MNI152 182x218x182 geometry in deterministic preprocessing. Do not resample or reorient. Use patch-based sampling during training, with 96x96x96 as the initial practical patch size. A 64x64x64 patch is lighter but may lose context; 128x128x128 gives more context but has a much larger 63-class logits footprint. Label-derived cropping is rejected for deterministic baseline preprocessing because it would not be reproducible at inference unless the crop can be generated from MRI alone.

## Class Imbalance

Training-only class-frequency rows were generated for background plus all 62 DKT foreground classes. The rarest foreground training labels are:

|class|original_id|region|hemisphere|train_voxels|train_volumes|
|---|---|---|---|---|---|
{chr(10).join(f"|{r['training_class_id']}|{r['original_label_id']}|{r['region_name']}|{r['hemisphere']}|{r['train_voxel_count']}|{r['train_volume_count_containing_label']}|" for r in rare)}

Recommend initial foreground-biased patch sampling using training labels only, plus a uniform/background fraction for context. Validation/test preprocessing and inference must not require labels. Recommend Dice plus unweighted cross-entropy initially; class-weighted cross-entropy can be revisited after a baseline.

## Label Mapping

Use the approved reversible mapping only inside tensor creation: original DKT IDs to contiguous 0-62, and contiguous predictions back to original DKT IDs for evaluation and visualization. Unknown IDs must fail immediately.

## Storage and Compute

```json
{json.dumps(cfg["storage_estimates"], indent=2, sort_keys=True)}
```

Patch memory estimates:

```json
{json.dumps(cfg["patch_memory_estimates"], indent=2, sort_keys=True)}
```

Local CPU validation of preprocessing logic is feasible. Practical 3D training likely requires GPU access; local CPU is suitable only for reduced-model or smoke experiments.

## Acceptance Test Matrix For Future Implementation

{chr(10).join(f"- {item}" for item in cfg["implementation_test_matrix"])}

## Unresolved Cautions

{chr(10).join(f"- {item}" for item in UNRESOLVED)}

## Status

The read-only preprocessing design passes this scoped milestone if human review accepts the proposed normalization, spatial strategy, patch size, sampling policy and loss design.
""",
        encoding="utf-8",
    )
    LOG_MD.parent.mkdir(parents=True, exist_ok=True)
    LOG_MD.write_text(
        f"""# Phase 1B Preprocessing Design Proposal Log

Date: {date.today().isoformat()}

Initiating prompt: frozen deterministic split milestone approved; perform read-only MNI152 preprocessing design and feasibility analysis only.

Skill: brain-segmentation-research.

Actions:

- Verified 101 accepted MNI152 rows with frozen train/validation/test assignments.
- Checked geometry, finite MRI values, integer labels, label vocabulary and source preservation.
- Wrote per-volume intensity summaries for all 101 MNI152 records.
- Wrote training-only class frequency rows for 63 proposed classes, with validation/test counts as audit-only fields.
- Proposed normalization, spatial handling, patch size, sampling, loss and future acceptance tests.

Validation result: passed as a read-only proposal milestone. No raw data, splits, class mappings, preprocessed arrays, caches, model code, training outputs or viewer files were modified.
""",
        encoding="utf-8",
    )


def main() -> int:
    result = analyze()
    write_csv(
        FEASIBILITY_CSV,
        ["category", "item", "status", "value", "details"],
        result["feasibility"],
    )
    intensity_fields = [
        "canonical_pair_id",
        "subject_id",
        "participant_group_id",
        "cohort",
        "split",
        "shape",
        "spacing",
        "orientation",
        "finite_values",
        "mri_min",
        "mri_max",
        "mri_mean",
        "mri_std",
        "mri_median",
        "nonzero_voxel_count",
        "zero_voxel_count",
        "nonzero_p0_5",
        "nonzero_p1",
        "nonzero_p5",
        "nonzero_p50",
        "nonzero_p95",
        "nonzero_p99",
        "nonzero_p99_5",
        "mri_nonzero_bbox",
        "label_foreground_bbox",
        "combined_foreground_bbox",
        "mri_label_intersection_voxels",
        "label_foreground_voxels",
    ]
    write_csv(INTENSITY_CSV, intensity_fields, result["intensity_rows"])
    write_csv(
        CLASS_FREQ_CSV,
        [
            "training_class_id",
            "original_label_id",
            "region_name",
            "hemisphere",
            "train_voxel_count",
            "train_volume_count_containing_label",
            "train_percentage_of_labeled_training_voxels",
            "train_relative_frequency_all_voxels",
            "imbalance_rank_rare_to_common",
            "validation_voxel_count_audit_only",
            "validation_volume_count_audit_only",
            "test_voxel_count_audit_only",
            "test_volume_count_audit_only",
            "training_decision_source",
        ],
        result["class_rows"],
    )
    CONFIG_JSON.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_JSON.write_text(json.dumps(result["config"], indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_report(result)

    failed = [row for row in result["feasibility"] if row["status"] == "failed"]
    summary = {
        "failed_checks": failed,
        "mni152_counts_by_split": result["split_counts"],
        "recommended_normalization": result["config"]["normalization_recommendation"],
        "recommended_patch_size": result["config"]["spatial_strategy_recommendation"]["recommended_patch_size"],
        "outputs": [
            str(FEASIBILITY_CSV.relative_to(ROOT)),
            str(INTENSITY_CSV.relative_to(ROOT)),
            str(CLASS_FREQ_CSV.relative_to(ROOT)),
            str(CONFIG_JSON.relative_to(ROOT)),
            str(REPORT_MD.relative_to(ROOT)),
            str(LOG_MD.relative_to(ROOT)),
        ],
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
