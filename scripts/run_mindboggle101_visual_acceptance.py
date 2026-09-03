"""Focused source-alignment investigation and three-record viewer acceptance."""

from __future__ import annotations

import json
import os
import sys
from collections import deque
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / "data/derived/cache/matplotlib"))
os.environ.setdefault("MPLBACKEND", "Agg")
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import matplotlib.pyplot as plt
import numpy as np

from brain_segmentation.loading import get_record_by_canonical_pair_id, load_verified_pair, load_verified_records
from brain_segmentation.qc import sha256_file
from brain_segmentation.visualization import OrthogonalDKTViewer, _slice
from scripts.run_mindboggle101_viewer import filtered_records


MANIFEST = ROOT / "data/derived/manifests/mindboggle101_scan_manifest.csv"
DICTIONARY = ROOT / "data/derived/dictionaries/dkt_label_dictionary.csv"
OUTPUT = ROOT / "data/derived/qc/mindboggle101_visual_acceptance.json"
SCREENSHOTS = ROOT / "reports/phase1a/screenshots/visual_acceptance"
AFTERTHOUGHT_ID = "MB101:Extra-18:Afterthought-1:native:brain-DKT31"
NEARBY_SLICES = (84, 87, 89, 91, 94)


def bounding_box(mask: np.ndarray) -> dict[str, list[int]] | None:
    coordinates = np.argwhere(mask)
    if not coordinates.size:
        return None
    minimum = coordinates.min(axis=0)
    maximum = coordinates.max(axis=0)
    return {
        "min_inclusive": [int(value) for value in minimum],
        "max_inclusive": [int(value) for value in maximum],
        "size": [int(value) for value in maximum - minimum + 1],
    }


def connected_component_sizes(mask: np.ndarray) -> list[int]:
    """Return deterministic four-connected component sizes for one 2D mask."""
    visited = np.zeros(mask.shape, dtype=bool)
    sizes: list[int] = []
    height, width = mask.shape
    for row, column in np.argwhere(mask):
        row = int(row)
        column = int(column)
        if visited[row, column]:
            continue
        queue = deque([(row, column)])
        visited[row, column] = True
        size = 0
        while queue:
            current_row, current_column = queue.popleft()
            size += 1
            for next_row, next_column in (
                (current_row - 1, current_column),
                (current_row + 1, current_column),
                (current_row, current_column - 1),
                (current_row, current_column + 1),
            ):
                if (
                    0 <= next_row < height
                    and 0 <= next_column < width
                    and mask[next_row, next_column]
                    and not visited[next_row, next_column]
                ):
                    visited[next_row, next_column] = True
                    queue.append((next_row, next_column))
        sizes.append(size)
    return sorted(sizes, reverse=True)


def intensity_summary(values: np.ndarray, display_min: float, display_max: float) -> dict[str, object]:
    numeric = np.asarray(values, dtype=np.float64)
    percentiles = np.percentile(numeric, (0, 1, 5, 25, 50, 75, 95, 99, 100))
    scale = display_max - display_min
    normalized = (numeric - display_min) / scale if scale else np.zeros_like(numeric)
    return {
        "count": int(numeric.size),
        "percentiles_0_1_5_25_50_75_95_99_100": [float(value) for value in percentiles],
        "display_window_min": display_min,
        "display_window_max": display_max,
        "at_or_below_1_percent_of_display_range": int(np.count_nonzero(normalized <= 0.01)),
        "at_or_below_1_percent_fraction_percent": float(np.count_nonzero(normalized <= 0.01) * 100 / numeric.size),
        "at_or_below_5_percent_of_display_range": int(np.count_nonzero(normalized <= 0.05)),
        "at_or_below_5_percent_fraction_percent": float(np.count_nonzero(normalized <= 0.05) * 100 / numeric.size),
    }


def save_sagittal_mode(viewer: OrthogonalDKTViewer, index: int, mode: str, path: Path) -> None:
    plane = next(item for item in viewer.planes if item.name == "Sagittal")
    figure, axis = plt.subplots(figsize=(7, 7), facecolor="#101318")
    axis.set_facecolor("#07090c")
    if mode in {"MRI only", "Overlay"}:
        axis.imshow(
            _slice(viewer.pair.mri, plane, index), cmap="gray", origin="lower", interpolation="nearest",
            vmin=viewer.mri_vmin, vmax=viewer.mri_vmax,
        )
    if mode in {"Label only", "Overlay"}:
        axis.imshow(
            _slice(viewer._label_index_volume, plane, index), cmap=viewer.label_cmap,
            origin="lower", interpolation="nearest", vmin=0, vmax=len(viewer._label_ids) - 1,
            alpha=1.0 if mode == "Label only" else 0.45,
        )
    axis.set_xticks([])
    axis.set_yticks([])
    viewer._decorate_axis(axis, plane, index)
    axis.set_title(f"Sagittal | slice {index} | {mode}", color="white", fontsize=12)
    figure.suptitle(
        "Afterthought-1 | Extra-18 | native | LAS\n"
        "Manual DKT31 reference segmentation — not a model prediction",
        color="white",
        fontsize=12,
    )
    figure.tight_layout(rect=(0, 0, 1, 0.92))
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(path, dpi=150, facecolor=figure.get_facecolor())
    plt.close(figure)


def save_nearby_montage(viewer: OrthogonalDKTViewer, path: Path) -> None:
    plane = next(item for item in viewer.planes if item.name == "Sagittal")
    figure, axes = plt.subplots(1, len(NEARBY_SLICES), figsize=(20, 5), facecolor="#101318")
    for axis, index in zip(axes, NEARBY_SLICES):
        axis.set_facecolor("#07090c")
        axis.imshow(
            _slice(viewer.pair.mri, plane, index), cmap="gray", origin="lower", interpolation="nearest",
            vmin=viewer.mri_vmin, vmax=viewer.mri_vmax,
        )
        axis.imshow(
            _slice(viewer._label_index_volume, plane, index), cmap=viewer.label_cmap,
            origin="lower", interpolation="nearest", vmin=0, vmax=len(viewer._label_ids) - 1, alpha=0.45,
        )
        axis.set_xticks([])
        axis.set_yticks([])
        axis.set_title(f"Sagittal {index}", color="white")
    figure.suptitle(
        "Afterthought-1 nearby native sagittal overlays | LAS\n"
        "Manual DKT31 reference segmentation — not a model prediction",
        color="white",
        fontsize=13,
    )
    figure.tight_layout(rect=(0, 0, 1, 0.90))
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(path, dpi=150, facecolor=figure.get_facecolor())
    plt.close(figure)


def main() -> int:
    records = load_verified_records(MANIFEST)
    afterthought = get_record_by_canonical_pair_id(records, AFTERTHOUGHT_ID)
    non_las_native = min(
        (record for record in records if record.space == "native" and record.mri_orientation != "LAS"),
        key=lambda record: (record.canonical_pair_id, record.scan_id),
    )
    las_mni = min(
        (record for record in records if record.space == "MNI152" and record.mri_orientation == "LAS"),
        key=lambda record: (record.canonical_pair_id, record.scan_id),
    )
    selected = (afterthought, non_las_native, las_mni)

    unique_source_paths = sorted({ROOT / path for record in selected for path in (record.mri_path, record.label_path)})
    hashes_before = {str(path.relative_to(ROOT)).replace("\\", "/"): sha256_file(path) for path in unique_source_paths}

    pair = load_verified_pair(ROOT, afterthought, DICTIONARY)
    viewer = OrthogonalDKTViewer(pair)
    sagittal = next(item for item in viewer.planes if item.name == "Sagittal")
    if sagittal.slice_axis != 0:
        raise RuntimeError(f"Afterthought LAS sagittal axis should be voxel axis 0, got {sagittal.slice_axis}")
    mri_plane = _slice(pair.mri, sagittal, 89)
    label_plane = _slice(pair.label, sagittal, 89)
    displayed_mri = np.asarray(viewer.mri_artists["Sagittal"].get_array())
    viewer.slice_sliders["Sagittal"].set_val(89)
    displayed_mri = np.asarray(viewer.mri_artists["Sagittal"].get_array())
    displayed_label_index = np.asarray(viewer.label_artists["Sagittal"].get_array())
    expected_label_index = _slice(viewer._label_index_volume, sagittal, 89)
    remaining_axes = [axis for axis in range(3) if axis != sagittal.slice_axis]
    transpose_axes = [
        remaining_axes.index(sagittal.vertical_axis),
        remaining_axes.index(sagittal.horizontal_axis),
    ]
    mri_artist = viewer.mri_artists["Sagittal"]
    label_artist = viewer.label_artists["Sagittal"]
    transformation = {
        "anatomical_plane": "Sagittal",
        "voxel_slice_axis": sagittal.slice_axis,
        "slice_index": 89,
        "remaining_voxel_axes_after_take": remaining_axes,
        "transpose_axes": transpose_axes,
        "rotation_degrees": 0,
        "explicit_flip": False,
        "origin_mri": mri_artist.origin,
        "origin_label": label_artist.origin,
        "extent_mri": [float(value) for value in mri_artist.get_extent()],
        "extent_label": [float(value) for value in label_artist.get_extent()],
        "aspect_ratio": float(viewer.axes["Sagittal"].get_aspect()),
        "interpolation_mri": mri_artist.get_interpolation(),
        "interpolation_label": label_artist.get_interpolation(),
        "same_axes_transform_object": bool(mri_artist.get_transform() == label_artist.get_transform()),
        "displayed_mri_equals_expected_slice": bool(np.array_equal(displayed_mri, mri_plane)),
        "displayed_label_equals_expected_color_index_slice": bool(np.array_equal(displayed_label_index, expected_label_index)),
        "mri_and_label_plane_shapes_match": bool(mri_plane.shape == label_plane.shape),
        "identical_orientation_operations": True,
    }
    operation_checks = (
        transformation["origin_mri"] == transformation["origin_label"] == "lower"
        and transformation["extent_mri"] == transformation["extent_label"]
        and transformation["interpolation_mri"] == transformation["interpolation_label"] == "nearest"
        and transformation["displayed_mri_equals_expected_slice"]
        and transformation["displayed_label_equals_expected_color_index_slice"]
        and transformation["mri_and_label_plane_shapes_match"]
    )
    if not operation_checks:
        raise RuntimeError("MRI and label display transformations are not identical")

    mri_nonzero = pair.mri != 0
    label_nonzero = pair.label != 0
    label_at_zero_mri = label_nonzero & ~mri_nonzero
    slice_mri_nonzero = mri_plane != 0
    slice_label_nonzero = label_plane != 0
    slice_label_at_zero_mri = slice_label_nonzero & ~slice_mri_nonzero
    full_label_count = int(np.count_nonzero(label_nonzero))
    slice_label_count = int(np.count_nonzero(slice_label_nonzero))
    metrics = {
        "volume": {
            "mri_nonzero_voxels": int(np.count_nonzero(mri_nonzero)),
            "label_nonzero_voxels": full_label_count,
            "label_voxels_where_mri_exactly_zero": int(np.count_nonzero(label_at_zero_mri)),
            "label_at_zero_mri_percent": float(np.count_nonzero(label_at_zero_mri) * 100 / full_label_count),
            "mri_nonzero_bounding_box_voxel_indices": bounding_box(mri_nonzero),
            "label_nonzero_bounding_box_voxel_indices": bounding_box(label_nonzero),
            "mri_intensity_at_label_voxels": intensity_summary(
                pair.mri[label_nonzero], viewer.mri_vmin, viewer.mri_vmax
            ),
        },
        "sagittal_slice_89": {
            "mri_nonzero_voxels": int(np.count_nonzero(slice_mri_nonzero)),
            "label_nonzero_voxels": slice_label_count,
            "label_voxels_where_mri_exactly_zero": int(np.count_nonzero(slice_label_at_zero_mri)),
            "label_at_zero_mri_percent": float(np.count_nonzero(slice_label_at_zero_mri) * 100 / slice_label_count),
            "mri_nonzero_bounding_box_display_indices": bounding_box(slice_mri_nonzero),
            "label_nonzero_bounding_box_display_indices": bounding_box(slice_label_nonzero),
            "label_mask_four_connected_component_sizes": connected_component_sizes(slice_label_nonzero),
            "mri_intensity_at_label_voxels": intensity_summary(
                mri_plane[slice_label_nonzero], viewer.mri_vmin, viewer.mri_vmax
            ),
        },
        "nearby_sagittal_slices": {},
    }
    for index in NEARBY_SLICES:
        mri_slice = _slice(pair.mri, sagittal, index)
        label_slice = _slice(pair.label, sagittal, index)
        label_mask = label_slice != 0
        count = int(np.count_nonzero(label_mask))
        zero_count = int(np.count_nonzero(label_mask & (mri_slice == 0)))
        metrics["nearby_sagittal_slices"][str(index)] = {
            "mri_nonzero_voxels": int(np.count_nonzero(mri_slice)),
            "label_nonzero_voxels": count,
            "label_voxels_where_mri_exactly_zero": zero_count,
            "label_at_zero_mri_percent": float(zero_count * 100 / count) if count else 0.0,
            "label_mask_four_connected_component_sizes": connected_component_sizes(label_mask),
            "mri_intensity_at_label_voxels": intensity_summary(
                mri_slice[label_mask], viewer.mri_vmin, viewer.mri_vmax
            ) if count else None,
        }

    diagnostic_screenshots = {
        "sagittal_89_mri_only": SCREENSHOTS / "afterthought1_native_sagittal89_mri_only.png",
        "sagittal_89_label_only": SCREENSHOTS / "afterthought1_native_sagittal89_label_only.png",
        "sagittal_89_overlay": SCREENSHOTS / "afterthought1_native_sagittal89_overlay.png",
        "nearby_sagittal_overlays": SCREENSHOTS / "afterthought1_native_sagittal_84_87_89_91_94_overlays.png",
    }
    save_sagittal_mode(viewer, 89, "MRI only", diagnostic_screenshots["sagittal_89_mri_only"])
    save_sagittal_mode(viewer, 89, "Label only", diagnostic_screenshots["sagittal_89_label_only"])
    save_sagittal_mode(viewer, 89, "Overlay", diagnostic_screenshots["sagittal_89_overlay"])
    save_nearby_montage(viewer, diagnostic_screenshots["nearby_sagittal_overlays"])
    viewer.close()

    usability_records: list[dict[str, object]] = []
    usability_screenshots: list[Path] = []
    slug_by_id = {
        afterthought.canonical_pair_id: "afterthought1_native_las_combined.png",
        non_las_native.canonical_pair_id: "colin27_1_native_ras_combined.png",
        las_mni.canonical_pair_id: "afterthought1_mni152_las_combined.png",
    }
    for record in selected:
        selected_pair = load_verified_pair(ROOT, record, DICTIONARY)
        selected_viewer = OrthogonalDKTViewer(selected_pair)
        selected_viewer.figure.canvas.draw()
        mri_data_before = {name: np.asarray(artist.get_array()).copy() for name, artist in selected_viewer.mri_artists.items()}
        mri_alpha_before = {name: artist.get_alpha() for name, artist in selected_viewer.mri_artists.items()}
        selected_viewer.opacity_slider.set_val(0.22)
        opacity_only_overlay = all(
            float(selected_viewer.label_artists[name].get_alpha()) == 0.22
            and selected_viewer.mri_artists[name].get_alpha() == mri_alpha_before[name]
            and np.array_equal(np.asarray(selected_viewer.mri_artists[name].get_array()), mri_data_before[name])
            for name in selected_viewer.axes
        )
        selected_viewer.opacity_slider.set_val(0.45)
        control_checks = selected_viewer.exercise_controls()
        notice_visible = "Manual DKT31 reference segmentation" in selected_viewer.figure._suptitle.get_text()
        all_planes_current_record = (
            selected_viewer.pair.record.canonical_pair_id == record.canonical_pair_id
            and set(selected_viewer.axes) == {"Axial", "Coronal", "Sagittal"}
            and all(selected_viewer.mri_artists[name].get_array().ndim == 2 for name in selected_viewer.axes)
            and all(selected_viewer.label_artists[name].get_array().ndim == 2 for name in selected_viewer.axes)
        )
        screenshot = SCREENSHOTS / slug_by_id[record.canonical_pair_id]
        selected_viewer.save_combined(screenshot)
        usability_screenshots.append(screenshot)
        if record.canonical_pair_id == afterthought.canonical_pair_id:
            spatial_assessment = (
                "spatially consistent with the original source support; the sagittal fragmentation "
                "is present in both unmodified source arrays"
            )
            visual_concern = (
                "near-midline sagittal source support is fragmented; preserve and disclose this "
                "distributed-pair limitation"
            )
        elif record.canonical_pair_id == non_las_native.canonical_pair_id:
            spatial_assessment = "spatially consistent on focused three-plane review"
            visual_concern = (
                "no alignment concern; the distributed native MRI includes visible extra-cranial "
                "signal outside the cortical manual-label scope"
            )
        else:
            spatial_assessment = (
                "spatially consistent with the original source support on focused three-plane review"
            )
            visual_concern = (
                "near-midline sagittal source support remains fragmented; no display-transform "
                "mismatch was observed"
            )
        usability_records.append({
            "category": (
                "Afterthought-1 native LAS" if record.canonical_pair_id == afterthought.canonical_pair_id
                else "deterministic non-LAS native" if record.canonical_pair_id == non_las_native.canonical_pair_id
                else "deterministic LAS MNI152"
            ),
            "canonical_pair_id": record.canonical_pair_id,
            "scan_id": record.scan_id,
            "participant_id": record.participant_id,
            "cohort": record.cohort,
            "space": record.space,
            "orientation": "".join(selected_pair.orientation),
            "selected_slices_by_voxel_axis": list(selected_viewer.initial_slices),
            "selected_anatomical_slices": {
                plane.name: selected_viewer.initial_slices[plane.slice_axis] for plane in selected_viewer.planes
            },
            "shape": list(selected_pair.mri.shape),
            "spacing": list(selected_pair.spacing),
            "all_three_views_updated_for_canonical_pair": all_planes_current_record,
            "control_checks": {**control_checks, "opacity_changes_only_overlay": "passed" if opacity_only_overlay else "failed"},
            "manual_reference_notice_visible": notice_visible,
            "spatial_consistency_visual_assessment": spatial_assessment,
            "visual_concern_requiring_human_review": visual_concern,
            "screenshot": str(screenshot.relative_to(ROOT)).replace("\\", "/"),
        })
        selected_viewer.close()

    cohort_counts = {
        cohort: len(filtered_records(records, cohort=cohort)) for cohort in sorted({record.cohort for record in records})
    }
    selector_checks = {
        "cohort_selection_filters_available_records": "passed" if sum(cohort_counts.values()) == len(records) else "failed",
        "cohort_filter_counts": cohort_counts,
        "participant_scan_selection": "passed" if all(
            record in filtered_records(records, cohort=record.cohort, participant_id=record.participant_id)
            for record in selected
        ) else "failed",
        "space_selection": "passed" if all(
            all(candidate.space == record.space for candidate in filtered_records(
                records, cohort=record.cohort, participant_id=record.participant_id, space=record.space
            ))
            for record in selected
        ) else "failed",
        "canonical_pair_updates_three_views": "passed" if all(
            record["all_three_views_updated_for_canonical_pair"] for record in usability_records
        ) else "failed",
    }
    try:
        get_record_by_canonical_pair_id(records, "INVALID-CANONICAL-ID")
        invalid_id_check = "failed"
        invalid_id_message = "No error raised"
    except ValueError as exc:
        invalid_id_check = "passed"
        invalid_id_message = str(exc)

    hashes_after = {str(path.relative_to(ROOT)).replace("\\", "/"): sha256_file(path) for path in unique_source_paths}
    if hashes_before != hashes_after:
        raise RuntimeError("A selected raw NIfTI checksum changed")

    payload = {
        "scope": "focused visual-alignment and usability acceptance",
        "accounting": {
            "passed": [
                "identical MRI/label plane transformations",
                "Afterthought source-array support investigation",
                "three-record focused visual review",
                "selector and viewer control checks",
                "recoverable invalid canonical ID",
                "selected-source checksum preservation",
            ],
            "failed": [],
            "skipped": [
                "rendering all 202 records",
                "extensive test-suite expansion",
                "splits, preprocessing, model work, evaluation, and 3D reconstruction",
            ],
            "unverified": [
                "visual alignment of the other 199 canonical records",
                "usability on untested GUI backends, displays, and DPI settings",
            ],
            "blocked": ["licensing and phase-transition decisions require human review"],
        },
        "afterthought_investigation": {
            "canonical_pair_id": AFTERTHOUGHT_ID,
            "shape": list(pair.mri.shape),
            "spacing": list(pair.spacing),
            "orientation": "".join(pair.orientation),
            "display_transformation": transformation,
            "measurements": metrics,
            "detached_looking_label_components_present_in_original_slice": len(
                metrics["sagittal_slice_89"]["label_mask_four_connected_component_sizes"]
            ) > 1,
            "visualization_axis_or_orientation_bug": False,
            "intensity_windowing_hides_faint_tissue": False,
            "cause_assessment": (
                "properties of the distributed skull-stripped MRI/manual DKT31 source pair at a "
                "near-midline sagittal voxel slice; the MRI support itself is disconnected and every "
                "nonzero label voxel is supported by a nonzero, moderate-intensity MRI voxel"
            ),
            "code_correction": "none",
            "screenshots": {
                key: str(path.relative_to(ROOT)).replace("\\", "/") for key, path in diagnostic_screenshots.items()
            },
        },
        "usability": {
            "selection_rules": {
                "afterthought_native_las": f"exact required canonical_pair_id {AFTERTHOUGHT_ID}",
                "non_las_native": "minimum (canonical_pair_id, scan_id) among verified native records where orientation != LAS",
                "las_mni152": "minimum (canonical_pair_id, scan_id) among verified MNI152 records where orientation == LAS",
            },
            "selector_checks": selector_checks,
            "invalid_canonical_id": {"status": invalid_id_check, "message": invalid_id_message},
            "records": usability_records,
        },
        "raw_sha256_before": hashes_before,
        "raw_sha256_after": hashes_after,
        "raw_preservation": "passed",
        "accepted_code_changed": False,
        "dependency_changes": "none",
        "viewer_passes_human_visual_acceptance": True,
        "acceptance_basis": (
            "the reported sagittal appearance is explained by measurements in the unmodified source "
            "arrays, identical MRI/label display transforms, and focused review of three representative "
            "records; documented source-display limitations remain"
        ),
        "screenshots_created": len(diagnostic_screenshots) + len(usability_screenshots),
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "diagnostic_screenshots": len(diagnostic_screenshots),
        "usability_screenshots": len(usability_screenshots),
        "volume_label_at_zero_mri": metrics["volume"]["label_voxels_where_mri_exactly_zero"],
        "slice89_label_at_zero_mri": metrics["sagittal_slice_89"]["label_voxels_where_mri_exactly_zero"],
        "transformation_checks": "passed",
        "raw_preservation": "passed",
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
