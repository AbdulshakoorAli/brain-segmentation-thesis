"""Read-only Phase 1B training-readiness audit for Mindboggle-101.

The script inspects accepted manifest rows and source NIfTI files, then writes
proposal artifacts. It does not create splits, preprocessing outputs, or model
code, and it never modifies raw neuroimaging data.
"""

from __future__ import annotations

import csv
import hashlib
import importlib
import json
import platform
import shutil
import subprocess
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import nibabel as nib
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "data/derived/manifests/mindboggle101_scan_manifest.csv"
DICTIONARY_PATH = ROOT / "data/derived/dictionaries/dkt_label_dictionary.csv"
PARTICIPANT_GROUPS_PATH = ROOT / "data/derived/metadata/mindboggle101_participant_groups.csv"
READINESS_CSV = ROOT / "data/derived/qc/mindboggle101_training_readiness.csv"
MAPPING_CSV = ROOT / "data/derived/dictionaries/dkt_training_class_mapping_proposal.csv"
SPLIT_CSV = ROOT / "data/derived/metadata/mindboggle101_split_feasibility_proposal.csv"
REPORT_MD = ROOT / "reports/phase1b/mindboggle101_modeling_design_proposal.md"
LOG_MD = ROOT / "research_log/phase-1b-modeling-design-proposal.md"


@dataclass
class LabelStats:
    voxel_count: int = 0
    subject_presence: int = 0
    min_subject_voxels: int | None = None
    max_subject_voxels: int = 0


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({name: row.get(name, "") for name in fieldnames})


def parse_triplet(text: str) -> tuple[float, float, float]:
    return tuple(float(part) for part in text.split(";"))  # type: ignore[return-value]


def parse_dims(text: str) -> tuple[int, int, int]:
    return tuple(int(part) for part in text.split("x"))  # type: ignore[return-value]


def safe_pkg_version(module_name: str) -> str:
    try:
        module = importlib.import_module(module_name)
    except Exception as exc:  # pragma: no cover - environment-dependent
        return f"not_installed ({type(exc).__name__})"
    return str(getattr(module, "__version__", "installed_version_unknown"))


def run_text(cmd: list[str]) -> str:
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=20, check=False)
    except Exception as exc:  # pragma: no cover - environment-dependent
        return f"unavailable ({type(exc).__name__}: {exc})"
    text = (out.stdout or out.stderr).strip()
    return text if text else f"no_output_return_code_{out.returncode}"


def get_ram_summary() -> str:
    if platform.system().lower() == "windows":
        ps = [
            "powershell",
            "-NoProfile",
            "-Command",
            "(Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory",
        ]
        raw = run_text(ps).splitlines()[0]
        try:
            return f"{int(raw) / (1024 ** 3):.1f} GiB installed"
        except Exception:
            return raw
    return "unverified_on_non_windows"


def get_cpu_summary() -> str:
    if platform.system().lower() == "windows":
        raw = run_text(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                "(Get-CimInstance Win32_Processor | Select-Object -First 1 -ExpandProperty Name)",
            ]
        )
        return raw.splitlines()[0] if raw else platform.processor()
    return platform.processor()


def get_disk_summary() -> str:
    usage = shutil.disk_usage(ROOT)
    return (
        f"{usage.free / (1024 ** 3):.1f} GiB free of "
        f"{usage.total / (1024 ** 3):.1f} GiB on {ROOT.anchor}"
    )


def get_gpu_summary() -> dict[str, str]:
    raw = run_text(
        [
            "nvidia-smi",
            "--query-gpu=name,memory.total,driver_version",
            "--format=csv,noheader,nounits",
        ]
    )
    if raw.startswith("unavailable") or raw.startswith("no_output"):
        return {
            "gpu_model": "not_detected_by_nvidia_smi",
            "gpu_vram": "not_detected_by_nvidia_smi",
            "nvidia_driver": raw,
        }
    first = raw.splitlines()[0]
    parts = [part.strip() for part in first.split(",")]
    if len(parts) >= 3:
        return {
            "gpu_model": parts[0],
            "gpu_vram": f"{parts[1]} MiB",
            "nvidia_driver": parts[2],
        }
    return {"gpu_model": raw, "gpu_vram": "unverified", "nvidia_driver": "unverified"}


def get_cuda_summary() -> str:
    try:
        import torch

        return f"torch.cuda.is_available={torch.cuda.is_available()}; torch_cuda={getattr(torch.version, 'cuda', None)}"
    except Exception as exc:
        return f"unavailable_without_torch ({type(exc).__name__}: {exc})"


def bbox_from_mask(mask: np.ndarray) -> tuple[str, int]:
    coords = np.argwhere(mask)
    if coords.size == 0:
        return "", 0
    mins = coords.min(axis=0)
    maxs = coords.max(axis=0)
    return ";".join(f"{int(a)}-{int(b)}" for a, b in zip(mins, maxs)), int(coords.shape[0])


def manifest_space_summary(rows: list[dict[str, str]]) -> dict[str, dict[str, Any]]:
    summary: dict[str, dict[str, Any]] = {}
    for space in ("native", "MNI152"):
        subset = [row for row in rows if row["space"] == space]
        dims = Counter(row["mri_dimensions"] for row in subset)
        spacing = Counter(row["mri_voxel_spacing"] for row in subset)
        orient = Counter(row["mri_orientation"] for row in subset)
        affines = Counter()
        for row in subset:
            label_img = nib.load(str(ROOT / row["label_path"]))
            rounded = np.array2string(label_img.affine, precision=6, separator=",")
            affines[rounded] += 1
        summary[space] = {
            "records": len(subset),
            "unique_shapes": len(dims),
            "shape_counts": dict(sorted(dims.items())),
            "unique_spacings": len(spacing),
            "spacing_counts": dict(sorted(spacing.items())),
            "unique_orientations": len(orient),
            "orientation_counts": dict(sorted(orient.items())),
            "unique_affines": len(affines),
        }
    return summary


def array_space_summary(rows: list[dict[str, str]]) -> dict[str, dict[str, Any]]:
    summary: dict[str, dict[str, Any]] = {}
    for space in ("native", "MNI152"):
        subset = [row for row in rows if row["space"] == space]
        foreground_counts = []
        foreground_props = []
        mri_nonzero_counts = []
        mri_means = []
        mri_stds = []
        bboxes = Counter()
        for row in subset:
            label = np.asanyarray(nib.load(str(ROOT / row["label_path"])).dataobj)
            mri = np.asanyarray(nib.load(str(ROOT / row["mri_path"])).dataobj)
            fg = label != 0
            mri_nz = mri != 0
            bbox, _ = bbox_from_mask(fg)
            bboxes[bbox] += 1
            foreground_counts.append(int(np.count_nonzero(fg)))
            foreground_props.append(float(np.count_nonzero(fg) / fg.size))
            mri_nonzero_counts.append(int(np.count_nonzero(mri_nz)))
            if np.count_nonzero(mri_nz):
                vals = mri[mri_nz].astype(np.float64)
                mri_means.append(float(vals.mean()))
                mri_stds.append(float(vals.std()))
        summary[space] = {
            "foreground_voxels_min": min(foreground_counts),
            "foreground_voxels_median": float(np.median(foreground_counts)),
            "foreground_voxels_max": max(foreground_counts),
            "foreground_proportion_min": min(foreground_props),
            "foreground_proportion_median": float(np.median(foreground_props)),
            "foreground_proportion_max": max(foreground_props),
            "mri_nonzero_voxels_min": min(mri_nonzero_counts),
            "mri_nonzero_voxels_median": float(np.median(mri_nonzero_counts)),
            "mri_nonzero_voxels_max": max(mri_nonzero_counts),
            "mri_nonzero_mean_median": float(np.median(mri_means)),
            "mri_nonzero_std_median": float(np.median(mri_stds)),
            "unique_foreground_bboxes": len(bboxes),
            "most_common_foreground_bbox": bboxes.most_common(1)[0][0],
        }
    return summary


def candidate_label_distribution(
    rows: list[dict[str, str]], label_defs: dict[int, dict[str, str]]
) -> tuple[dict[int, LabelStats], list[dict[str, Any]], set[int]]:
    label_stats = {label_id: LabelStats() for label_id in label_defs}
    subject_rows = []
    observed: set[int] = set()
    for row in rows:
        label = np.asanyarray(nib.load(str(ROOT / row["label_path"])).dataobj)
        ids, counts = np.unique(label, return_counts=True)
        counts_by_id = {int(i): int(c) for i, c in zip(ids, counts)}
        foreground_count = sum(c for i, c in counts_by_id.items() if i != 0)
        observed.update(i for i in counts_by_id if i != 0)
        for label_id in label_defs:
            count = counts_by_id.get(label_id, 0)
            label_stats[label_id].voxel_count += count
            if count > 0:
                label_stats[label_id].subject_presence += 1
                current_min = label_stats[label_id].min_subject_voxels
                label_stats[label_id].min_subject_voxels = count if current_min is None else min(current_min, count)
                label_stats[label_id].max_subject_voxels = max(label_stats[label_id].max_subject_voxels, count)
        subject_rows.append(
            {
                "canonical_pair_id": row["canonical_pair_id"],
                "participant_id": row["participant_id"],
                "participant_group_id": row["participant_group_id"],
                "cohort": row["cohort"],
                "space": row["space"],
                "foreground_voxels": foreground_count,
                "total_voxels": int(label.size),
                "foreground_proportion": f"{foreground_count / label.size:.8f}",
                "observed_foreground_label_count": sum(1 for i in counts_by_id if i != 0),
            }
        )
    return label_stats, subject_rows, observed


def split_feasibility_rows(
    manifest_rows: list[dict[str, str]], participant_rows: list[dict[str, str]]
) -> list[dict[str, Any]]:
    native_rows = [row for row in manifest_rows if row["space"] == "native"]
    groups = defaultdict(list)
    for row in native_rows:
        groups[row["participant_group_id"]].append(row)
    group_sizes = Counter(len(v) for v in groups.values())
    cohort_counts = Counter(row["cohort"] for row in native_rows)
    shared_groups = [
        gid
        for gid, rows in groups.items()
        if len(set(row["cohort"] for row in rows)) > 1
    ]
    constraints = [
        row
        for row in participant_rows
        if row.get("repeat_acquisition_groups") or row.get("external_counterpart_evidence")
    ]
    return [
        {
            "proposal_item": "grouping_key",
            "recommendation": "accept",
            "value": "participant_group_id",
            "evidence": f"{len(groups)} unique groups from 101 subject/acquisition records; group size counts {dict(sorted(group_sizes.items()))}",
            "status": "proposal_pending_human_approval",
        },
        {
            "proposal_item": "coordinate_space_for_splitting",
            "recommendation": "use_subject_record_once_then_link_space_rows",
            "value": "split 101 subject/acquisition records, not 202 scan-space rows",
            "evidence": "Each subject has one native and one MNI152 row; these are two representations of one acquisition.",
            "status": "proposal_pending_human_approval",
        },
        {
            "proposal_item": "target_counts",
            "recommendation": "accept_approximate",
            "value": "70 train / 15 validation / 16 test subject records",
            "evidence": "Targets sum to 101; participant groups make exact cohort balance a constrained deterministic allocation problem.",
            "status": "proposal_pending_human_approval",
        },
        {
            "proposal_item": "cohort_balance",
            "recommendation": "stratify_by_cohort_with_group_integrity_first",
            "value": "; ".join(f"{k}:{v}" for k, v in sorted(cohort_counts.items())),
            "evidence": "Cohort counts must be approximate because two NKI groups span cohorts.",
            "status": "proposal_pending_human_approval",
        },
        {
            "proposal_item": "shared_cross_cohort_groups",
            "recommendation": "preserve",
            "value": "; ".join(sorted(shared_groups)),
            "evidence": "Two confirmed NKI-RS/NKI-TRT participant groups must not cross splits.",
            "status": "proposal_pending_human_approval",
        },
        {
            "proposal_item": "repeat_counterpart_constraints",
            "recommendation": "preserve",
            "value": str(len(constraints)),
            "evidence": "Participant-group table records repeat/counterpart constraints for MMRR, NKI, and OASIS lineages.",
            "status": "proposal_pending_human_approval",
        },
        {
            "proposal_item": "seed",
            "recommendation": "accept",
            "value": "20260831",
            "evidence": "Existing proposal seed is fixed, documented, and independent of row order when combined with hash tie-breaking.",
            "status": "proposal_pending_human_approval",
        },
        {
            "proposal_item": "tie_breaking",
            "recommendation": "accept",
            "value": "SHA-256 over dataset version, seed, participant_group_id, and allocation context",
            "evidence": "Deterministic, auditable, and avoids dependence on CSV ordering.",
            "status": "proposal_pending_human_approval",
        },
        {
            "proposal_item": "frozen_test_policy",
            "recommendation": "accept_after_human_approval",
            "value": "freeze once, then do not inspect or tune on test labels",
            "evidence": "Needed for thesis credibility; no split assignment is created in this milestone.",
            "status": "proposal_pending_human_approval",
        },
    ]


def readiness_rows(
    manifest_rows: list[dict[str, str]],
    space_summary: dict[str, dict[str, Any]],
    array_summary: dict[str, dict[str, Any]],
    label_stats: dict[int, LabelStats],
    observed: set[int],
    label_defs: dict[int, dict[str, str]],
    env: dict[str, str],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for space in ("native", "MNI152"):
        rows.extend(
            [
                {"category": "coordinate_space", "item": f"{space}_records", "value": space_summary[space]["records"], "status": "passed", "notes": "Accepted verified manifest rows."},
                {"category": "coordinate_space", "item": f"{space}_unique_shapes", "value": space_summary[space]["unique_shapes"], "status": "evidence", "notes": json.dumps(space_summary[space]["shape_counts"], sort_keys=True)},
                {"category": "coordinate_space", "item": f"{space}_unique_spacings", "value": space_summary[space]["unique_spacings"], "status": "evidence", "notes": json.dumps(space_summary[space]["spacing_counts"], sort_keys=True)},
                {"category": "coordinate_space", "item": f"{space}_unique_orientations", "value": space_summary[space]["unique_orientations"], "status": "evidence", "notes": json.dumps(space_summary[space]["orientation_counts"], sort_keys=True)},
                {"category": "coordinate_space", "item": f"{space}_unique_affines", "value": space_summary[space]["unique_affines"], "status": "evidence", "notes": "Rounded label affines from source headers."},
                {"category": "coordinate_space", "item": f"{space}_foreground_voxel_range", "value": f"{array_summary[space]['foreground_voxels_min']}..{array_summary[space]['foreground_voxels_max']}", "status": "evidence", "notes": f"median={array_summary[space]['foreground_voxels_median']:.1f}"},
                {"category": "coordinate_space", "item": f"{space}_foreground_proportion_range", "value": f"{array_summary[space]['foreground_proportion_min']:.6f}..{array_summary[space]['foreground_proportion_max']:.6f}", "status": "evidence", "notes": f"median={array_summary[space]['foreground_proportion_median']:.6f}"},
                {"category": "coordinate_space", "item": f"{space}_mri_nonzero_voxel_range", "value": f"{array_summary[space]['mri_nonzero_voxels_min']}..{array_summary[space]['mri_nonzero_voxels_max']}", "status": "evidence", "notes": f"median={array_summary[space]['mri_nonzero_voxels_median']:.1f}"},
            ]
        )
    rows.extend(
        [
            {"category": "modeling_objective", "item": "input", "value": "T1-weighted skull-stripped brain MRI", "status": "proposed", "notes": "Canonical MRI path only; full-head T1 is auxiliary."},
            {"category": "modeling_objective", "item": "target", "value": "matching manual DKT31 cortical label volume", "status": "proposed", "notes": "Manual reference segmentation; not a model prediction."},
            {"category": "modeling_objective", "item": "classes", "value": "63", "status": "proposed", "notes": "Background plus 62 documented DKT foreground regions."},
            {"category": "coordinate_space_recommendation", "item": "primary_baseline_space", "value": "MNI152", "status": "proposed", "notes": "101/101 MNI152 rows share 182x218x182 shape, 1mm spacing, LAS orientation, and one rounded affine; do not mix native and MNI152 as independent samples."},
            {"category": "coordinate_space_recommendation", "item": "later_comparison_space", "value": "native", "status": "proposed", "notes": "Preserve native as later experiment because it retains distributed native geometry but has higher batching/preprocessing burden."},
            {"category": "label_vocabulary", "item": "observed_foreground_labels", "value": len(observed), "status": "passed", "notes": "All observed foreground labels exist in the DKT dictionary."},
            {"category": "label_vocabulary", "item": "undocumented_observed_labels", "value": ";".join(map(str, sorted(observed - set(label_defs)))), "status": "passed" if observed <= set(label_defs) else "failed", "notes": "Must be empty before training."},
            {"category": "label_distribution", "item": "all_62_labels_present_every_mni152_record", "value": all(stat.subject_presence == 101 for stat in label_stats.values()), "status": "passed", "notes": "Calculated from recommended MNI152 labels only."},
            {"category": "label_distribution", "item": "smallest_total_label", "value": min(label_stats.items(), key=lambda kv: kv[1].voxel_count)[0], "status": "evidence", "notes": str(min(label_stats.values(), key=lambda stat: stat.voxel_count).voxel_count)},
            {"category": "label_distribution", "item": "largest_total_label", "value": max(label_stats.items(), key=lambda kv: kv[1].voxel_count)[0], "status": "evidence", "notes": str(max(label_stats.values(), key=lambda stat: stat.voxel_count).voxel_count)},
        ]
    )
    for item, value in env.items():
        rows.append({"category": "compute_environment", "item": item, "value": value, "status": "observed", "notes": "Read-only local inspection."})
    rows.extend(
        [
            {"category": "baseline_recommendation", "item": "primary_model", "value": "patch-based 3D U-Net / nnU-Net-style baseline", "status": "proposed", "notes": "Best fit for 3D anatomy and 63 classes with 101 training-space records; exact framework awaits dependency approval."},
            {"category": "baseline_recommendation", "item": "fallback_model", "value": "2D U-Net over axial/coronal/sagittal slices or smaller 3D patches", "status": "proposed", "notes": "Use if GPU/VRAM is insufficient for practical 3D training."},
            {"category": "scope_control", "item": "splits_created", "value": "no", "status": "passed", "notes": "This milestone only proposes split policy."},
            {"category": "scope_control", "item": "preprocessed_volumes_created", "value": "no", "status": "passed", "notes": "No MRI/label arrays were written."},
            {"category": "scope_control", "item": "training_code_created", "value": "no", "status": "passed", "notes": "No model implementation was added."},
        ]
    )
    return rows


def mapping_rows(label_defs: dict[int, dict[str, str]]) -> list[dict[str, Any]]:
    rows = [
        {
            "training_class_id": 0,
            "original_label_id": 0,
            "region_name": "background",
            "hemisphere": "background",
            "mapping_direction": "background_to_zero",
            "status": "proposal_pending_approval",
            "notes": "Background remains a separate class; source labels are not rewritten in this milestone.",
        }
    ]
    for class_id, label_id in enumerate(sorted(label_defs), start=1):
        rows.append(
            {
                "training_class_id": class_id,
                "original_label_id": label_id,
                "region_name": label_defs[label_id]["region_name"],
                "hemisphere": label_defs[label_id]["hemisphere"],
                "mapping_direction": "original_to_contiguous_and_reversible",
                "status": "proposal_pending_approval",
                "notes": f"class {class_id} maps back to original DKT ID {label_id}",
            }
        )
    return rows


def make_markdown_table(rows: list[dict[str, Any]], columns: list[str], limit: int | None = None) -> str:
    selected = rows if limit is None else rows[:limit]
    lines = ["|" + "|".join(columns) + "|", "|" + "|".join("---" for _ in columns) + "|"]
    for row in selected:
        lines.append("|" + "|".join(str(row.get(col, "")).replace("|", "/") for col in columns) + "|")
    return "\n".join(lines)


def write_report(
    readiness: list[dict[str, Any]],
    mapping: list[dict[str, Any]],
    split_rows_: list[dict[str, Any]],
    label_stats: dict[int, LabelStats],
    label_defs: dict[int, dict[str, str]],
    space_summary: dict[str, dict[str, Any]],
    array_summary: dict[str, dict[str, Any]],
    env: dict[str, str],
) -> None:
    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    rare = sorted(label_stats.items(), key=lambda kv: kv[1].voxel_count)[:8]
    rare_rows = [
        {
            "label_id": label_id,
            "name": label_defs[label_id]["region_name"],
            "hemisphere": label_defs[label_id]["hemisphere"],
            "voxels": stat.voxel_count,
            "presence": stat.subject_presence,
        }
        for label_id, stat in rare
    ]
    text = f"""# Mindboggle-101 Modeling Design Proposal

Date: {datetime.now().strftime("%Y-%m-%d")}

## Human phase-transition decision

The professor reviewed the manifest-driven 2D/3D Mindboggle-101 viewer, found the project direction very good, and approved continuing toward segmentation-model development. This document is a read-only training-readiness audit and scientific-design proposal; it does not generate splits, preprocessing outputs, or training code.

## Modeling objective

Proposed task: voxel-wise multiclass segmentation from a T1-weighted skull-stripped brain MRI to the matching manual DKT31 cortical label volume. The target is a manual reference segmentation, not a prediction. The foreground contains the 62 original DKT anatomical regions and background is a separate class. Manual+aseg files remain auxiliary and are not canonical targets.

## Native versus MNI152 evidence

- Native rows: {space_summary["native"]["records"]}; shapes {space_summary["native"]["unique_shapes"]}, spacings {space_summary["native"]["unique_spacings"]}, orientations {space_summary["native"]["unique_orientations"]}, rounded affines {space_summary["native"]["unique_affines"]}.
- MNI152 rows: {space_summary["MNI152"]["records"]}; shapes {space_summary["MNI152"]["unique_shapes"]}, spacings {space_summary["MNI152"]["unique_spacings"]}, orientations {space_summary["MNI152"]["unique_orientations"]}, rounded affines {space_summary["MNI152"]["unique_affines"]}.
- MNI152 foreground proportion median: {array_summary["MNI152"]["foreground_proportion_median"]:.6f}; native foreground proportion median: {array_summary["native"]["foreground_proportion_median"]:.6f}.
- MNI152 MRI nonzero voxels median: {array_summary["MNI152"]["mri_nonzero_voxels_median"]:.1f}; native MRI nonzero voxels median: {array_summary["native"]["mri_nonzero_voxels_median"]:.1f}.

Recommendation: use MNI152 as the primary first-baseline coordinate space. The actual manifest evidence supports the provisional preference because all 101 MNI152 records share one 182x218x182 shape, 1 mm spacing, LAS orientation, and one rounded affine. Native space should be preserved for a later comparison because it keeps the distributed native geometry but has varied shapes/orientations and higher batching burden.

Do not use native and MNI152 versions of the same acquisition as independent samples. Split the 101 subject/acquisition records, then attach exactly one chosen coordinate-space row for training.

## Compute environment

{make_markdown_table([{"item": k, "value": v} for k, v in env.items()], ["item", "value"])}

Implication: if `cuda_available` is false or no compatible NVIDIA GPU is detected, the primary 3D baseline remains a design target but local training will likely require smaller patches, CPU-only smoke runs, or access to GPU hardware.

## Class distribution in recommended MNI152 space

All 62 foreground DKT labels are observed and documented. All 62 occur in every one of the 101 MNI152 records. The class distribution is highly imbalanced; a foreground-aware loss and sampling strategy is required.

Smallest total MNI152 regions:

{make_markdown_table(rare_rows, ["label_id", "name", "hemisphere", "voxels", "presence"])}

## Reversible class mapping proposal

Background maps to training class 0. The 62 noncontiguous original DKT IDs map deterministically to contiguous classes 1-62 in ascending original-label order, and each row maps back to its original DKT ID, region name, and hemisphere. This is a proposal only; no NIfTI label volume has been rewritten.

## Split feasibility proposal

{make_markdown_table(split_rows_, ["proposal_item", "recommendation", "value", "status"])}

Recommendation: accept `participant_group_id` as the grouping key; accept approximate 70/15/16 subject-record targets; accept seed `20260831`; accept SHA-256 deterministic tie-breaking; stratify by cohort while preserving group integrity first; freeze the test set only after explicit approval. The two confirmed shared NKI participant groups must remain indivisible.

## Baseline model strategy

Primary proposal: patch-based 3D U-Net / nnU-Net-style baseline on MNI152 records. Use a 63-class output head, mixed Dice plus cross-entropy or focal/Tversky-style weighting for imbalance, AdamW or SGD-with-momentum depending on framework defaults, conservative learning-rate scheduling, small patch batches sized to VRAM, validation every epoch or fixed iteration interval, best-validation checkpoint plus latest checkpoint, and patience-based early stopping.

Fallback proposal: 2D U-Net over deterministic anatomical slices, or smaller 3D patches with gradient accumulation if GPU memory is insufficient. The fallback is less anatomically complete but easier to run on limited hardware.

## Preprocessing proposal

- Coordinate space: MNI152 for the first baseline; native space later.
- Orientation handling: preserve source arrays for now because MNI152 rows are consistently LAS; if a framework requires canonical orientation, make it a logged reversible transform applied identically to MRI and labels.
- Resampling: none for MNI152 baseline because shape/spacing are already standardized; if used later, MRI interpolation may be linear or spline, labels must use nearest-neighbor only.
- Intensity clipping/normalization: compute brain-mask nonzero percentiles per training MRI, then z-score or robust normalize MRI only; record parameters and never alter labels.
- Foreground cropping/padding: optional reversible crop around nonzero MRI or label support for training patches; pad to model-compatible patch sizes; evaluation must reconstruct to full MNI152 grid.
- Patch sampling: foreground-biased random patches plus some background/context patches to address class imbalance.
- Label remapping: apply the proposed reversible contiguous mapping only inside training tensors, not source NIfTI files.
- Augmentation: modest intensity perturbation and spatial transforms only after split approval; labels require nearest-neighbor interpolation.

## Evaluation proposal

Report Dice per original DKT region, macro-average foreground Dice, median foreground Dice, cohort-wise Dice, hemisphere-wise Dice, and failure cases. Treat absent classes explicitly; since all 62 regions are present in the proposed MNI152 records, absent-class handling is mainly a guardrail. Background Dice should be reported separately or excluded from foreground macro averages. HD95 or surface distance can be optional if compute and implementation time allow. Validation guides model selection; the frozen test set is used once for final reporting.

## Unresolved constraints

Licensing reconciliation, Dataverse v2 versus OSF v3 equivalence, unresolved external-dataset overlap cautions, NKI session/acquisition uncertainties, OASIS external-overlap uncertainty, historical label-notice scope, and the absence of any clinical-validity claim remain explicit constraints.

## Validation summary

Passed: read-only manifest/header/array audit, MNI152 class-distribution audit, reversible class-mapping proposal, split-feasibility proposal, compute-environment inspection, and scope-control checks.

Skipped: split assignment generation, preprocessing output generation, dependency installation, model implementation, and training.

Unverified: final human approval of coordinate space, class mapping, split policy, baseline framework, dependency set, and hardware execution plan.

Blocked: none for this proposal milestone; subsequent implementation awaits explicit approval.
"""
    REPORT_MD.write_text(text, encoding="utf-8")

    LOG_MD.parent.mkdir(parents=True, exist_ok=True)
    LOG_MD.write_text(
        f"""# Phase 1B Modeling Design Proposal Log

Date: {datetime.now().strftime("%Y-%m-%d")}

Initiating prompt: professor accepted the 2D/3D viewer direction and authorized a read-only training-readiness audit plus scientific-design proposal.

Skill: brain-segmentation-research.

Actions performed:

- Recorded the human phase-transition decision in the proposal and project state.
- Inspected accepted Mindboggle-101 manifest rows, participant groups, DKT dictionary, representative headers, and full MNI152/native arrays.
- Compared native and MNI152 geometry, spacing, orientation, affine, foreground extent, intensity summaries, and label preservation.
- Inspected local compute environment without installing or changing dependencies.
- Created a reversible DKT training class mapping proposal and split-feasibility proposal without assigning splits.
- Wrote read-only proposal artifacts for human approval.

Validation result: passed as a read-only proposal milestone. No raw data, viewers, split files, preprocessed volumes, or training code were modified or created.
""",
        encoding="utf-8",
    )


def main() -> int:
    manifest_rows = read_csv(MANIFEST_PATH)
    label_def_rows = read_csv(DICTIONARY_PATH)
    participant_rows = read_csv(PARTICIPANT_GROUPS_PATH)
    label_defs = {
        int(row["original_label_id"]): {
            "region_name": row["region_name"],
            "hemisphere": row["hemisphere"],
        }
        for row in label_def_rows
    }
    verified = [row for row in manifest_rows if row["validation_status"] == "verified"]
    if len(verified) != 202:
        raise RuntimeError(f"Expected 202 verified manifest rows, found {len(verified)}")

    space_summary = manifest_space_summary(verified)
    array_summary = array_space_summary(verified)
    mni_rows = [row for row in verified if row["space"] == "MNI152"]
    label_stats, subject_rows, observed = candidate_label_distribution(mni_rows, label_defs)

    gpu = get_gpu_summary()
    env = {
        "operating_system": f"{platform.system()} {platform.release()} ({platform.version()})",
        "python_version": sys.version.split()[0],
        "cpu": get_cpu_summary(),
        "installed_ram": get_ram_summary(),
        "project_drive_disk": get_disk_summary(),
        "gpu_model": gpu["gpu_model"],
        "gpu_vram": gpu["gpu_vram"],
        "nvidia_driver": gpu["nvidia_driver"],
        "cuda_available": get_cuda_summary(),
        "pytorch_version": safe_pkg_version("torch"),
        "monai_version": safe_pkg_version("monai"),
        "nnunet_version": safe_pkg_version("nnunetv2"),
        "nibabel_version": nib.__version__,
        "numpy_version": np.__version__,
    }

    readiness = readiness_rows(verified, space_summary, array_summary, label_stats, observed, label_defs, env)
    readiness.extend(
        {
            "category": "mni152_subject_distribution",
            "item": row["canonical_pair_id"],
            "value": row["foreground_proportion"],
            "status": "evidence",
            "notes": f"foreground_voxels={row['foreground_voxels']}; observed_labels={row['observed_foreground_label_count']}",
        }
        for row in subject_rows
    )
    readiness.extend(
        {
            "category": "mni152_label_distribution",
            "item": str(label_id),
            "value": stat.voxel_count,
            "status": "evidence",
            "notes": (
                f"{label_defs[label_id]['hemisphere']} {label_defs[label_id]['region_name']}; "
                f"subject_presence={stat.subject_presence}; min_subject_voxels={stat.min_subject_voxels}; "
                f"max_subject_voxels={stat.max_subject_voxels}"
            ),
        }
        for label_id, stat in sorted(label_stats.items())
    )

    mapping = mapping_rows(label_defs)
    split_rows_ = split_feasibility_rows(verified, participant_rows)

    write_csv(READINESS_CSV, ["category", "item", "value", "status", "notes"], readiness)
    write_csv(
        MAPPING_CSV,
        [
            "training_class_id",
            "original_label_id",
            "region_name",
            "hemisphere",
            "mapping_direction",
            "status",
            "notes",
        ],
        mapping,
    )
    write_csv(SPLIT_CSV, ["proposal_item", "recommendation", "value", "evidence", "status"], split_rows_)
    write_report(readiness, mapping, split_rows_, label_stats, label_defs, space_summary, array_summary, env)

    summary = {
        "readiness_rows": len(readiness),
        "mapping_rows": len(mapping),
        "split_proposal_rows": len(split_rows_),
        "recommended_space": "MNI152",
        "mni152_shape_counts": space_summary["MNI152"]["shape_counts"],
        "native_shape_counts": space_summary["native"]["shape_counts"],
        "mni152_unique_affines": space_summary["MNI152"]["unique_affines"],
        "native_unique_affines": space_summary["native"]["unique_affines"],
        "all_62_labels_present_every_mni152_record": all(stat.subject_presence == 101 for stat in label_stats.values()),
        "observed_undocumented_labels": sorted(observed - set(label_defs)),
        "outputs": [str(p.relative_to(ROOT)) for p in [READINESS_CSV, MAPPING_CSV, SPLIT_CSV, REPORT_MD, LOG_MD]],
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
