"""Derived manual-DKT31 meshes and professor-demo rendering helpers."""

from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import nibabel as nib
import numpy as np
import plotly.graph_objects as go
from matplotlib import pyplot as plt
from skimage.measure import marching_cubes

from brain_segmentation.loading import LoadedCanonicalPair
from brain_segmentation.visualization import (
    _color_for_id,
    _orientation_edges,
    _slice,
    planes_for_orientation,
    segmentation_center,
)


MESH_FORMAT_VERSION = 1
MESH_ALGORITHM = "scikit-image marching_cubes Lewiner level=0.5 step_size=1 padded_binary_mask"
DISPLAY_MESH_ALGORITHM = "scikit-image marching_cubes Lewiner level=0.5 step_size=2 padded_binary_mask"
PLOTLY_STREAMLIT_CONFIG = {
    "scrollZoom": True,
    "displaylogo": False,
    "responsive": True,
    "modeBarButtonsToRemove": ["lasso3d", "select2d"],
}


@dataclass(frozen=True)
class DktRegion:
    label_id: int
    name: str
    hemisphere: str
    color_hex: str


@dataclass(frozen=True)
class RegionMesh:
    region: DktRegion
    vertices_path: Path
    faces_path: Path
    vertex_count: int
    face_count: int
    display_vertices_path: Path
    display_faces_path: Path
    display_vertex_count: int
    display_face_count: int

    def load(self, *, display: bool = False) -> tuple[np.ndarray, np.ndarray]:
        vertices_path = self.display_vertices_path if display else self.vertices_path
        faces_path = self.display_faces_path if display else self.faces_path
        vertices = np.load(vertices_path, allow_pickle=False, mmap_mode="r")
        faces = np.load(faces_path, allow_pickle=False, mmap_mode="r")
        return vertices, faces


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def deterministic_color_hex(label_id: int) -> str:
    red, green, blue, _ = _color_for_id(label_id)
    channels = (round(red * 255), round(green * 255), round(blue * 255))
    return "#" + "".join(f"{value:02x}" for value in channels)


def load_dkt_regions(dictionary_path: Path) -> dict[int, DktRegion]:
    with dictionary_path.open(newline="", encoding="utf-8-sig") as stream:
        rows = list(csv.DictReader(stream))
    regions: dict[int, DktRegion] = {}
    for row in rows:
        label_id = int(row["original_label_id"])
        hemisphere = row["hemisphere"].strip().lower()
        if hemisphere not in {"left", "right"}:
            raise ValueError(f"Unsupported hemisphere for DKT ID {label_id}: {hemisphere!r}")
        regions[label_id] = DktRegion(
            label_id=label_id,
            name=row["region_name"].strip(),
            hemisphere=hemisphere,
            color_hex=deterministic_color_hex(label_id),
        )
    return regions


def build_region_meshes(
    pair: LoadedCanonicalPair,
    *,
    project_root: Path,
    dictionary_path: Path,
    output_dir: Path,
    progress_callback: Callable[[int, int, int], None] | None = None,
) -> dict[str, object]:
    """Generate exact step-1 surfaces from one read-only categorical label volume."""
    regions = load_dkt_regions(dictionary_path)
    observed = tuple(value for value in pair.observed_label_ids if value != 0)
    unknown = sorted(set(observed) - set(regions))
    if unknown:
        raise ValueError(f"Observed label IDs are absent from the accepted DKT dictionary: {unknown}")

    output_dir.mkdir(parents=True, exist_ok=True)
    mesh_rows: list[dict[str, object]] = []
    for region_index, label_id in enumerate(observed, start=1):
        region = regions[label_id]
        mask = np.asarray(pair.label == label_id, dtype=np.uint8)
        padded = np.pad(mask, 1, mode="constant", constant_values=0)
        vertices, faces, _, _ = marching_cubes(
            padded,
            level=0.5,
            step_size=1,
            allow_degenerate=False,
            method="lewiner",
        )
        voxel_vertices = vertices.astype(np.float64, copy=False) - 1.0
        world_vertices = nib.affines.apply_affine(pair.affine, voxel_vertices).astype("<f4", copy=False)
        mesh_faces = faces.astype("<u4", copy=False)
        display_vertices, display_faces, _, _ = marching_cubes(
            padded,
            level=0.5,
            step_size=2,
            allow_degenerate=False,
            method="lewiner",
        )
        display_voxel_vertices = display_vertices.astype(np.float64, copy=False) - 1.0
        display_world_vertices = nib.affines.apply_affine(
            pair.affine, display_voxel_vertices
        ).astype("<f4", copy=False)
        display_mesh_faces = display_faces.astype("<u4", copy=False)
        vertices_name = f"label_{label_id}_vertices.npy"
        faces_name = f"label_{label_id}_faces.npy"
        display_vertices_name = f"label_{label_id}_display_vertices.npy"
        display_faces_name = f"label_{label_id}_display_faces.npy"
        np.save(output_dir / vertices_name, world_vertices, allow_pickle=False)
        np.save(output_dir / faces_name, mesh_faces, allow_pickle=False)
        np.save(output_dir / display_vertices_name, display_world_vertices, allow_pickle=False)
        np.save(output_dir / display_faces_name, display_mesh_faces, allow_pickle=False)
        mesh_rows.append({
            "label_id": label_id,
            "region_name": region.name,
            "hemisphere": region.hemisphere,
            "color_hex": region.color_hex,
            "source_voxel_count": int(np.count_nonzero(mask)),
            "vertex_count": int(world_vertices.shape[0]),
            "face_count": int(mesh_faces.shape[0]),
            "vertices_file": vertices_name,
            "faces_file": faces_name,
            "display_vertex_count": int(display_world_vertices.shape[0]),
            "display_face_count": int(display_mesh_faces.shape[0]),
            "display_vertices_file": display_vertices_name,
            "display_faces_file": display_faces_name,
            "vertices_sha256": sha256_file(output_dir / vertices_name),
            "faces_sha256": sha256_file(output_dir / faces_name),
            "display_vertices_sha256": sha256_file(output_dir / display_vertices_name),
            "display_faces_sha256": sha256_file(output_dir / display_faces_name),
            "world_bounds": {
                "minimum": [float(value) for value in np.min(world_vertices, axis=0)],
                "maximum": [float(value) for value in np.max(world_vertices, axis=0)],
            },
        })
        if progress_callback is not None:
            progress_callback(region_index, len(observed), label_id)

    mri_path = project_root / pair.record.mri_path
    label_path = project_root / pair.record.label_path
    payload: dict[str, object] = {
        "format_version": MESH_FORMAT_VERSION,
        "algorithm": MESH_ALGORITHM,
        "display_algorithm": DISPLAY_MESH_ALGORITHM,
        "canonical_pair_id": pair.record.canonical_pair_id,
        "scan_id": pair.record.scan_id,
        "participant_id": pair.record.participant_id,
        "cohort": pair.record.cohort,
        "space": pair.record.space,
        "shape": list(pair.label.shape),
        "spacing": list(pair.spacing),
        "orientation": "".join(pair.orientation),
        "affine": pair.affine.tolist(),
        "mri_path": pair.record.mri_path,
        "label_path": pair.record.label_path,
        "mri_sha256": sha256_file(mri_path),
        "label_sha256": sha256_file(label_path),
        "dictionary_path": str(dictionary_path.relative_to(project_root)).replace("\\", "/"),
        "dictionary_sha256": sha256_file(dictionary_path),
        "background_meshed": False,
        "affine_application_count": 1,
        "voxel_spacing_applied_separately": False,
        "disconnected_components_preserved": True,
        "source_values_modified": False,
        "regions": mesh_rows,
    }
    all_minimum = np.min(
        np.asarray([row["world_bounds"]["minimum"] for row in mesh_rows], dtype=np.float64), axis=0
    )
    all_maximum = np.max(
        np.asarray([row["world_bounds"]["maximum"] for row in mesh_rows], dtype=np.float64), axis=0
    )
    payload["world_bounds"] = {
        "minimum": [float(value) for value in all_minimum],
        "maximum": [float(value) for value in all_maximum],
    }
    manifest_path = output_dir / "mesh_manifest.json"
    manifest_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def load_region_meshes(output_dir: Path) -> tuple[RegionMesh, ...]:
    manifest_path = output_dir / "mesh_manifest.json"
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    meshes = []
    for row in payload["regions"]:
        meshes.append(RegionMesh(
            region=DktRegion(
                label_id=int(row["label_id"]),
                name=str(row["region_name"]),
                hemisphere=str(row["hemisphere"]),
                color_hex=str(row["color_hex"]),
            ),
            vertices_path=output_dir / str(row["vertices_file"]),
            faces_path=output_dir / str(row["faces_file"]),
            vertex_count=int(row["vertex_count"]),
            face_count=int(row["face_count"]),
            display_vertices_path=output_dir / str(row["display_vertices_file"]),
            display_faces_path=output_dir / str(row["display_faces_file"]),
            display_vertex_count=int(row["display_vertex_count"]),
            display_face_count=int(row["display_face_count"]),
        ))
    return tuple(sorted(meshes, key=lambda mesh: mesh.region.label_id))


def validate_region_meshes(meshes: tuple[RegionMesh, ...]) -> dict[str, object]:
    failures: list[str] = []
    for mesh in meshes:
        vertices, faces = mesh.load()
        if vertices.ndim != 2 or vertices.shape[1] != 3 or not np.all(np.isfinite(vertices)):
            failures.append(f"invalid vertices for {mesh.region.label_id}")
        if faces.ndim != 2 or faces.shape[1] != 3 or faces.size == 0:
            failures.append(f"invalid faces for {mesh.region.label_id}")
        elif int(np.max(faces)) >= len(vertices):
            failures.append(f"face index out of range for {mesh.region.label_id}")
        if len(vertices) != mesh.vertex_count or len(faces) != mesh.face_count:
            failures.append(f"manifest count mismatch for {mesh.region.label_id}")
        display_vertices, display_faces = mesh.load(display=True)
        if (
            display_vertices.ndim != 2
            or display_vertices.shape[1] != 3
            or not np.all(np.isfinite(display_vertices))
        ):
            failures.append(f"invalid display vertices for {mesh.region.label_id}")
        if display_faces.ndim != 2 or display_faces.shape[1] != 3 or display_faces.size == 0:
            failures.append(f"invalid display faces for {mesh.region.label_id}")
        elif int(np.max(display_faces)) >= len(display_vertices):
            failures.append(f"display face index out of range for {mesh.region.label_id}")
        if (
            len(display_vertices) != mesh.display_vertex_count
            or len(display_faces) != mesh.display_face_count
        ):
            failures.append(f"display manifest count mismatch for {mesh.region.label_id}")
    return {
        "status": "passed" if not failures else "failed",
        "region_count": len(meshes),
        "total_vertices": sum(mesh.vertex_count for mesh in meshes),
        "total_faces": sum(mesh.face_count for mesh in meshes),
        "total_display_vertices": sum(mesh.display_vertex_count for mesh in meshes),
        "total_display_faces": sum(mesh.display_face_count for mesh in meshes),
        "failures": failures,
    }


def build_3d_figure(
    meshes: tuple[RegionMesh, ...],
    selected_label_ids: set[int],
    *,
    opacity: float,
    uirevision: str = "mindboggle101-manual-dkt31",
) -> go.Figure:
    traces: list[go.Mesh3d] = []
    for mesh in meshes:
        if mesh.region.label_id not in selected_label_ids:
            continue
        vertices, faces = mesh.load(display=True)
        traces.append(go.Mesh3d(
            x=vertices[:, 0],
            y=vertices[:, 1],
            z=vertices[:, 2],
            i=faces[:, 0],
            j=faces[:, 1],
            k=faces[:, 2],
            color=mesh.region.color_hex,
            opacity=opacity,
            flatshading=False,
            lighting={"ambient": 0.48, "diffuse": 0.72, "specular": 0.15, "roughness": 0.72},
            lightposition={"x": 100, "y": -150, "z": 200},
            name=f"{mesh.region.label_id} — {mesh.region.hemisphere} {mesh.region.name}",
            hovertemplate=(
                f"ID {mesh.region.label_id}<br>{mesh.region.hemisphere} {mesh.region.name}"
                "<extra></extra>"
            ),
            showlegend=False,
        ))
    figure = go.Figure(data=traces)
    figure.update_layout(
        height=720,
        margin={"l": 0, "r": 0, "t": 48, "b": 0},
        paper_bgcolor="#0e1117",
        plot_bgcolor="#0e1117",
        font={"color": "#f2f2f2"},
        title={"text": "Manual DKT31 reference surfaces — not a model prediction", "x": 0.5},
        scene={
            "aspectmode": "data",
            "dragmode": "orbit",
            "xaxis": {"title": "world X (mm)", "backgroundcolor": "#151a22", "gridcolor": "#39404c"},
            "yaxis": {"title": "world Y (mm)", "backgroundcolor": "#151a22", "gridcolor": "#39404c"},
            "zaxis": {"title": "world Z (mm)", "backgroundcolor": "#151a22", "gridcolor": "#39404c"},
            "camera": {"eye": {"x": 1.45, "y": -1.65, "z": 1.05}},
        },
        uirevision=uirevision,
    )
    return figure


def build_orthogonal_figure(
    pair: LoadedCanonicalPair,
    slices_by_axis: tuple[int, int, int],
    *,
    mode: str,
    opacity: float,
    selected_label_ids: set[int] | None = None,
):
    planes = planes_for_orientation(pair.orientation)
    selected = selected_label_ids or set(value for value in pair.observed_label_ids if value)
    figure, axes = plt.subplots(1, 3, figsize=(13, 4.6), facecolor="#0e1117")
    mri_min = float(np.min(pair.mri))
    mri_max = float(np.max(pair.mri))
    for plane, axis in zip(planes, axes):
        index = slices_by_axis[plane.slice_axis]
        if mode in {"MRI only", "Overlay"}:
            axis.imshow(
                _slice(pair.mri, plane, index), cmap="gray", origin="lower",
                interpolation="nearest", vmin=mri_min, vmax=mri_max,
            )
        if mode in {"Label only", "Overlay"}:
            label_slice = np.rint(_slice(pair.label, plane, index)).astype(np.int32, copy=False)
            rgba = np.zeros((*label_slice.shape, 4), dtype=np.float32)
            for label_id in selected:
                rgba[label_slice == label_id] = _color_for_id(label_id)
            if mode == "Overlay":
                rgba[..., 3] *= opacity
            axis.imshow(rgba, origin="lower", interpolation="nearest")
        left, right, bottom, top = _orientation_edges(pair.orientation, plane)
        axis.set_title(f"{plane.name} · slice {index}", color="white", fontsize=10)
        style = {"color": "#ffd166", "fontsize": 9, "fontweight": "bold", "transform": axis.transAxes}
        axis.text(0.01, 0.5, left, ha="left", va="center", **style)
        axis.text(0.99, 0.5, right, ha="right", va="center", **style)
        axis.text(0.5, 0.01, bottom, ha="center", va="bottom", **style)
        axis.text(0.5, 0.99, top, ha="center", va="top", **style)
        axis.set_facecolor("#07090c")
        axis.set_xticks([])
        axis.set_yticks([])
    figure.suptitle(
        "Accepted orthogonal views · manual DKT31 reference, not a prediction",
        color="white",
        fontsize=11,
    )
    figure.tight_layout(rect=(0, 0, 1, 0.92))
    return figure


def initial_slices(pair: LoadedCanonicalPair) -> tuple[int, int, int]:
    return segmentation_center(pair.label)
