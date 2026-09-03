"""Build and validate the single-record Afterthought-1 3D professor demo."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("MPLBACKEND", "Agg")
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / "data/derived/cache/matplotlib"))
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import plotly  # noqa: E402
import skimage  # noqa: E402
import streamlit  # noqa: E402
from matplotlib.backends.backend_agg import FigureCanvasAgg  # noqa: E402
from mpl_toolkits.mplot3d.art3d import Poly3DCollection  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

from brain_segmentation.loading import (  # noqa: E402
    get_record_by_canonical_pair_id,
    load_verified_pair,
    load_verified_records,
)
from brain_segmentation.mesh_visualization import (  # noqa: E402
    PLOTLY_STREAMLIT_CONFIG,
    build_3d_figure,
    build_orthogonal_figure,
    build_region_meshes,
    initial_slices,
    load_dkt_regions,
    load_region_meshes,
    sha256_file,
    validate_region_meshes,
)


PAIR_ID = "MB101:Extra-18:Afterthought-1:native:brain-DKT31"
MANIFEST = ROOT / "data/derived/manifests/mindboggle101_scan_manifest.csv"
DICTIONARY = ROOT / "data/derived/dictionaries/dkt_label_dictionary.csv"
MESH_DIR = ROOT / "data/derived/visualization/afterthought1_native_dkt31_meshes"
SCREENSHOTS = ROOT / "reports/phase1a/screenshots/afterthought1_3d_professor_demo"
VALIDATION = ROOT / "data/derived/qc/afterthought1_3d_demo_validation.json"


def render_static_3d(meshes, selected_ids: set[int], path: Path, title: str) -> None:
    figure = plt.figure(figsize=(9, 8), facecolor="#0e1117")
    axis = figure.add_subplot(111, projection="3d", facecolor="#0e1117")
    minima: list[np.ndarray] = []
    maxima: list[np.ndarray] = []
    for mesh in meshes:
        if mesh.region.label_id not in selected_ids:
            continue
        vertices, faces = mesh.load(display=True)
        collection = Poly3DCollection(
            np.asarray(vertices)[np.asarray(faces)],
            facecolor=mesh.region.color_hex,
            edgecolor="none",
            alpha=0.90,
        )
        axis.add_collection3d(collection)
        minima.append(np.min(vertices, axis=0))
        maxima.append(np.max(vertices, axis=0))
    minimum = np.min(np.stack(minima), axis=0)
    maximum = np.max(np.stack(maxima), axis=0)
    center = (minimum + maximum) / 2.0
    span = maximum - minimum
    radius = float(np.max(span)) / 2.0
    axis.set_xlim(center[0] - radius, center[0] + radius)
    axis.set_ylim(center[1] - radius, center[1] + radius)
    axis.set_zlim(center[2] - radius, center[2] + radius)
    axis.set_box_aspect((1, 1, 1))
    axis.view_init(elev=16, azim=-76)
    axis.set_xlabel("world X (mm)", color="white")
    axis.set_ylabel("world Y (mm)", color="white")
    axis.set_zlabel("world Z (mm)", color="white")
    axis.tick_params(colors="#bdc5d1", labelsize=7)
    axis.set_title(title + "\nManual DKT31 reference — not a model prediction", color="white", fontsize=12)
    axis.grid(False)
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(path, dpi=150, facecolor=figure.get_facecolor(), bbox_inches="tight")
    plt.close(figure)


def combine_screenshots(three_d: Path, two_d: Path, output: Path) -> None:
    with Image.open(three_d) as left_source, Image.open(two_d) as right_source:
        left = left_source.convert("RGB")
        right = right_source.convert("RGB")
        height = max(left.height, right.height)
        left = left.resize((round(left.width * height / left.height), height))
        right = right.resize((round(right.width * height / right.height), height))
        heading = 64
        canvas = Image.new("RGB", (left.width + right.width, height + heading), "#0e1117")
        canvas.paste(left, (0, heading))
        canvas.paste(right, (left.width, heading))
        draw = ImageDraw.Draw(canvas)
        draw.text(
            (20, 18),
            "Afterthought-1 native professor demo | derived 3D + accepted 2D views | manual reference, not prediction",
            fill="white",
        )
        output.parent.mkdir(parents=True, exist_ok=True)
        canvas.save(output)


def main() -> None:
    records = load_verified_records(MANIFEST)
    record = get_record_by_canonical_pair_id(records, PAIR_ID)
    pair = load_verified_pair(ROOT, record, DICTIONARY)
    raw_paths = [ROOT / record.mri_path, ROOT / record.label_path]
    hashes_before = {str(path.relative_to(ROOT)).replace("\\", "/"): sha256_file(path) for path in raw_paths}

    mesh_manifest = build_region_meshes(
        pair,
        project_root=ROOT,
        dictionary_path=DICTIONARY,
        output_dir=MESH_DIR,
    )
    meshes = load_region_meshes(MESH_DIR)
    mesh_validation = validate_region_meshes(meshes)
    regions = load_dkt_regions(DICTIONARY)
    observed = {value for value in pair.observed_label_ids if value}
    all_ids = {mesh.region.label_id for mesh in meshes}
    left_ids = {mesh.region.label_id for mesh in meshes if mesh.region.hemisphere == "left"}
    right_ids = {mesh.region.label_id for mesh in meshes if mesh.region.hemisphere == "right"}

    all_figure = build_3d_figure(meshes, all_ids, opacity=0.82)
    left_figure = build_3d_figure(meshes, left_ids, opacity=0.82)
    right_figure = build_3d_figure(meshes, right_ids, opacity=0.82)
    figure_checks = {
        "all_region_trace_count": len(all_figure.data),
        "left_hemisphere_trace_count": len(left_figure.data),
        "right_hemisphere_trace_count": len(right_figure.data),
        "orbit_drag_mode": all_figure.layout.scene.dragmode == "orbit",
        "scroll_zoom_enabled": PLOTLY_STREAMLIT_CONFIG["scrollZoom"] is True,
        "hover_has_original_ids": all(
            f"ID {mesh.region.label_id}" in str(trace.hovertemplate)
            for mesh, trace in zip(meshes, all_figure.data)
        ),
        "region_filtering": len(left_figure.data) == len(left_ids) and len(right_figure.data) == len(right_ids),
    }

    centers = initial_slices(pair)
    two_d_checks: dict[str, object] = {}
    two_d_path = SCREENSHOTS / "afterthought1_accepted_2d_views.png"
    for mode in ("MRI only", "Label only", "Overlay"):
        figure = build_orthogonal_figure(pair, centers, mode=mode, opacity=0.45, selected_label_ids=all_ids)
        FigureCanvasAgg(figure).draw()
        two_d_checks[mode] = {
            "axes": len(figure.axes),
            "rendered": len(figure.axes) == 3,
        }
        if mode == "Overlay":
            two_d_path.parent.mkdir(parents=True, exist_ok=True)
            figure.savefig(two_d_path, dpi=150, facecolor=figure.get_facecolor(), bbox_inches="tight")
        plt.close(figure)

    all_path = SCREENSHOTS / "afterthought1_3d_all_regions.png"
    left_path = SCREENSHOTS / "afterthought1_3d_left_hemisphere.png"
    right_path = SCREENSHOTS / "afterthought1_3d_right_hemisphere.png"
    combined_path = SCREENSHOTS / "afterthought1_professor_demo_combined.png"
    render_static_3d(meshes, all_ids, all_path, "All 62 cortical DKT regions")
    render_static_3d(meshes, left_ids, left_path, "Left hemisphere · 31 DKT regions")
    render_static_3d(meshes, right_ids, right_path, "Right hemisphere · 31 DKT regions")
    combine_screenshots(all_path, two_d_path, combined_path)

    hashes_after = {str(path.relative_to(ROOT)).replace("\\", "/"): sha256_file(path) for path in raw_paths}
    screenshot_paths = (all_path, left_path, right_path, two_d_path, combined_path)
    validation = {
        "scope": "Afterthought-1 native interactive 3D professor-demo MVP",
        "canonical_pair_id": PAIR_ID,
        "manual_reference_not_prediction": True,
        "pair_validation": pair.validation,
        "shape": list(pair.mri.shape),
        "spacing": list(pair.spacing),
        "orientation": "".join(pair.orientation),
        "observed_label_ids": list(pair.observed_label_ids),
        "mesh": {
            **mesh_validation,
            "all_observed_foreground_ids_meshed": all_ids == observed == set(regions),
            "left_region_count": len(left_ids),
            "right_region_count": len(right_ids),
            "background_meshed": False,
            "algorithm": mesh_manifest["algorithm"],
            "display_algorithm": mesh_manifest["display_algorithm"],
            "source_voxel_count": sum(int(row["source_voxel_count"]) for row in mesh_manifest["regions"]),
        },
        "interactive_3d": figure_checks,
        "accepted_2d": {
            "selected_slices_by_voxel_axis": list(centers),
            "mode_rendering": two_d_checks,
            "same_read_only_loaded_pair": True,
        },
        "controls": {
            "rotation": "Plotly orbit drag mode",
            "zoom": "Plotly scroll zoom and modebar",
            "region": "Streamlit original-ID/name multiselect",
            "hemisphere": "independent left and right checkboxes",
            "surface_opacity": "Streamlit slider",
            "2d_slices": "one Streamlit slider per anatomical plane",
            "2d_mode": "MRI only, label only, or overlay",
            "2d_opacity": "Streamlit slider",
        },
        "dependency_versions": {
            "streamlit": streamlit.__version__,
            "plotly": plotly.__version__,
            "scikit-image": skimage.__version__,
        },
        "screenshots": [str(path.relative_to(ROOT)).replace("\\", "/") for path in screenshot_paths],
        "screenshot_sha256": {
            str(path.relative_to(ROOT)).replace("\\", "/"): sha256_file(path) for path in screenshot_paths
        },
        "source_sha256_before": hashes_before,
        "source_sha256_after": hashes_after,
        "source_preservation": "passed" if hashes_before == hashes_after else "failed",
        "split_files_created": 0,
        "other_record_meshes_created": 0,
    }
    failures = []
    if mesh_validation["status"] != "passed":
        failures.extend(mesh_validation["failures"])
    if not validation["mesh"]["all_observed_foreground_ids_meshed"]:
        failures.append("mesh ID coverage mismatch")
    if not all(value is True for key, value in figure_checks.items() if isinstance(value, bool)):
        failures.append("interactive figure validation failed")
    if any(not result["rendered"] for result in two_d_checks.values()):
        failures.append("2D mode rendering failed")
    if hashes_before != hashes_after:
        failures.append("source hash changed")
    validation["status"] = "passed" if not failures else "failed"
    validation["failures"] = failures
    VALIDATION.parent.mkdir(parents=True, exist_ok=True)
    VALIDATION.write_text(json.dumps(validation, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": validation["status"],
        "regions": len(meshes),
        "vertices": mesh_validation["total_vertices"],
        "faces": mesh_validation["total_faces"],
        "screenshots": len(screenshot_paths),
        "source_preservation": validation["source_preservation"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
