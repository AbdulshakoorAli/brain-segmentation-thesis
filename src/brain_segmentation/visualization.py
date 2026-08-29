"""Orthogonal MRI/manual-DKT31 visualization with interactive controls."""

from __future__ import annotations

import colorsys
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap
from matplotlib.widgets import RadioButtons, Slider

from brain_segmentation.loading import LoadedCanonicalPair


OPPOSITE = {"L": "R", "R": "L", "A": "P", "P": "A", "S": "I", "I": "S"}


@dataclass(frozen=True)
class Plane:
    name: str
    slice_axis: int
    horizontal_axis: int
    vertical_axis: int


def _anatomical_axis(orientation: tuple[str, str, str], codes: set[str]) -> int:
    matches = [axis for axis, code in enumerate(orientation) if code in codes]
    if len(matches) != 1:
        raise ValueError(f"Orientation {orientation} does not define one axis for {sorted(codes)}")
    return matches[0]


def planes_for_orientation(orientation: tuple[str, str, str]) -> tuple[Plane, Plane, Plane]:
    """Map voxel axes to anatomical planes without reorienting the volume."""
    left_right = _anatomical_axis(orientation, {"L", "R"})
    anterior_posterior = _anatomical_axis(orientation, {"A", "P"})
    superior_inferior = _anatomical_axis(orientation, {"S", "I"})
    return (
        Plane("Axial", superior_inferior, left_right, anterior_posterior),
        Plane("Coronal", anterior_posterior, left_right, superior_inferior),
        Plane("Sagittal", left_right, anterior_posterior, superior_inferior),
    )


def segmentation_center(label: np.ndarray) -> tuple[int, int, int]:
    """Return the integer center of the nonzero segmentation extent."""
    foreground = np.argwhere(label != 0)
    if not foreground.size:
        raise ValueError("Cannot select slices from an empty segmentation")
    minimum = foreground.min(axis=0)
    maximum = foreground.max(axis=0)
    return tuple(int(value) for value in ((minimum + maximum) // 2))


def _slice(volume: np.ndarray, plane: Plane, index: int) -> np.ndarray:
    sliced = np.take(volume, index, axis=plane.slice_axis)
    remaining_axes = [axis for axis in range(3) if axis != plane.slice_axis]
    vertical = remaining_axes.index(plane.vertical_axis)
    horizontal = remaining_axes.index(plane.horizontal_axis)
    return np.transpose(sliced, axes=(vertical, horizontal))


def _orientation_edges(orientation: tuple[str, str, str], plane: Plane) -> tuple[str, str, str, str]:
    right = orientation[plane.horizontal_axis]
    top = orientation[plane.vertical_axis]
    return OPPOSITE[right], right, OPPOSITE[top], top


def _color_for_id(label_id: int) -> tuple[float, float, float, float]:
    hue = (label_id * 0.618033988749895) % 1.0
    red, green, blue = colorsys.hsv_to_rgb(hue, 0.72, 1.0)
    return red, green, blue, 1.0


class OrthogonalDKTViewer:
    """Interactive three-plane viewer; all mappings are display-only."""

    def __init__(self, pair: LoadedCanonicalPair, *, opacity: float = 0.45):
        self.pair = pair
        self.planes = planes_for_orientation(pair.orientation)
        self.initial_slices = segmentation_center(pair.label)
        self.slice_indices = list(self.initial_slices)
        self.opacity = float(opacity)
        self.mode = "Overlay"
        self._label_ids = (0,) + tuple(sorted(pair.label_names))
        self._index_by_id = {label_id: index for index, label_id in enumerate(self._label_ids)}
        colors = [(0.0, 0.0, 0.0, 0.0)] + [_color_for_id(value) for value in self._label_ids[1:]]
        self.label_cmap = ListedColormap(colors, name="deterministic_dkt31")
        self._label_index_volume = self._make_label_index_volume(pair.label)
        self._label_index_volume.setflags(write=False)

        finite = pair.mri[np.isfinite(pair.mri)]
        self.mri_vmin = float(np.min(finite))
        self.mri_vmax = float(np.max(finite))
        self.figure, axes = plt.subplots(1, 3, figsize=(16, 9), facecolor="#101318")
        self.axes = dict(zip((plane.name for plane in self.planes), axes))
        self.figure.subplots_adjust(left=0.04, right=0.98, top=0.82, bottom=0.25, wspace=0.08)
        self.mri_artists = {}
        self.label_artists = {}
        self._build_panels()
        self._build_controls()
        self.figure.canvas.mpl_connect("button_press_event", self._on_click)

    def _make_label_index_volume(self, label: np.ndarray) -> np.ndarray:
        integer_labels = np.rint(label).astype(np.int32, copy=False)
        lookup = np.zeros(int(integer_labels.max()) + 1, dtype=np.uint8)
        for label_id, color_index in self._index_by_id.items():
            if label_id:
                lookup[label_id] = color_index
        return lookup[integer_labels]

    def _build_panels(self) -> None:
        record = self.pair.record
        for plane in self.planes:
            axis = self.axes[plane.name]
            index = self.slice_indices[plane.slice_axis]
            mri_artist = axis.imshow(
                _slice(self.pair.mri, plane, index),
                cmap="gray",
                origin="lower",
                interpolation="nearest",
                vmin=self.mri_vmin,
                vmax=self.mri_vmax,
            )
            label_artist = axis.imshow(
                _slice(self._label_index_volume, plane, index),
                cmap=self.label_cmap,
                origin="lower",
                interpolation="nearest",
                vmin=0,
                vmax=len(self._label_ids) - 1,
                alpha=self.opacity,
            )
            self.mri_artists[plane.name] = mri_artist
            self.label_artists[plane.name] = label_artist
            axis.set_facecolor("#07090c")
            axis.set_xticks([])
            axis.set_yticks([])
            self._decorate_axis(axis, plane, index)
        self.figure.suptitle(
            f"{record.participant_id} | {record.cohort} | {record.space} | "
            f"shape {'×'.join(str(v) for v in self.pair.mri.shape)} | "
            f"spacing {', '.join(f'{v:.6g}' for v in self.pair.spacing)} mm | "
            f"orientation {''.join(self.pair.orientation)}\n"
            "Manual DKT31 reference segmentation — not a model prediction",
            color="white",
            fontsize=14,
        )

    def _decorate_axis(self, axis, plane: Plane, index: int) -> None:
        left, right, bottom, top = _orientation_edges(self.pair.orientation, plane)
        axis.set_title(f"{plane.name} | slice {index}", color="white", fontsize=12)
        style = dict(color="#ffd166", fontsize=11, fontweight="bold", transform=axis.transAxes)
        axis.text(0.01, 0.5, left, ha="left", va="center", **style)
        axis.text(0.99, 0.5, right, ha="right", va="center", **style)
        axis.text(0.5, 0.01, bottom, ha="center", va="bottom", **style)
        axis.text(0.5, 0.99, top, ha="center", va="top", **style)

    def _build_controls(self) -> None:
        self.slice_sliders = {}
        slider_positions = {"Axial": 0.16, "Coronal": 0.115, "Sagittal": 0.07}
        for plane in self.planes:
            slider_axis = self.figure.add_axes([0.10, slider_positions[plane.name], 0.47, 0.025])
            slider = Slider(
                slider_axis,
                f"{plane.name} slice",
                0,
                self.pair.mri.shape[plane.slice_axis] - 1,
                valinit=self.slice_indices[plane.slice_axis],
                valstep=1,
            )
            slider.label.set_color("white")
            slider.valtext.set_color("white")
            slider.on_changed(lambda value, selected=plane: self._set_slice(selected, int(value)))
            self.slice_sliders[plane.name] = slider
        opacity_axis = self.figure.add_axes([0.72, 0.16, 0.22, 0.025])
        self.opacity_slider = Slider(opacity_axis, "Overlay opacity", 0.0, 1.0, valinit=self.opacity)
        self.opacity_slider.label.set_color("white")
        self.opacity_slider.valtext.set_color("white")
        self.opacity_slider.on_changed(self._set_opacity)
        mode_axis = self.figure.add_axes([0.72, 0.055, 0.12, 0.085], facecolor="#ececec")
        self.mode_selector = RadioButtons(mode_axis, ("MRI only", "Label only", "Overlay"), active=2)
        self.mode_selector.on_clicked(self._set_mode)
        self.label_status = self.figure.text(
            0.91,
            0.095,
            "Click a panel\nfor label ID / region",
            color="white",
            fontsize=9,
            ha="center",
            va="center",
        )

    def _set_slice(self, plane: Plane, index: int) -> None:
        self.slice_indices[plane.slice_axis] = index
        self.mri_artists[plane.name].set_data(_slice(self.pair.mri, plane, index))
        self.label_artists[plane.name].set_data(_slice(self._label_index_volume, plane, index))
        self.axes[plane.name].set_title(f"{plane.name} | slice {index}", color="white", fontsize=12)
        self.figure.canvas.draw_idle()

    def _set_opacity(self, value: float) -> None:
        self.opacity = float(value)
        for artist in self.label_artists.values():
            artist.set_alpha(self.opacity)
        self.figure.canvas.draw_idle()

    def _set_mode(self, mode: str) -> None:
        self.mode = mode
        for artist in self.mri_artists.values():
            artist.set_visible(mode in {"MRI only", "Overlay"})
        for artist in self.label_artists.values():
            artist.set_visible(mode in {"Label only", "Overlay"})
        self.figure.canvas.draw_idle()

    def _on_click(self, event) -> None:
        plane = next((item for item in self.planes if self.axes[item.name] is event.inaxes), None)
        if plane is None or event.xdata is None or event.ydata is None:
            return
        voxel = [0, 0, 0]
        voxel[plane.slice_axis] = self.slice_indices[plane.slice_axis]
        voxel[plane.horizontal_axis] = int(round(event.xdata))
        voxel[plane.vertical_axis] = int(round(event.ydata))
        if any(value < 0 or value >= self.pair.label.shape[axis] for axis, value in enumerate(voxel)):
            return
        label_id = int(round(float(self.pair.label[tuple(voxel)])))
        name = "background" if label_id == 0 else self.pair.label_names.get(label_id, "name unavailable")
        self.label_status.set_text(f"voxel {tuple(voxel)}\nID {label_id}: {name}")
        self.figure.canvas.draw_idle()

    def exercise_controls(self) -> dict[str, str]:
        """Programmatically exercise each widget using the loaded real pair."""
        for plane in self.planes:
            slider = self.slice_sliders[plane.name]
            target = min(int(slider.val) + 1, int(slider.valmax))
            slider.set_val(target)
            if self.slice_indices[plane.slice_axis] != target:
                raise RuntimeError(f"{plane.name} slice control did not update")
        self.opacity_slider.set_val(0.30)
        if not all(float(artist.get_alpha()) == 0.30 for artist in self.label_artists.values()):
            raise RuntimeError("Opacity control did not update all overlays")
        for index, expected in enumerate(("MRI only", "Label only", "Overlay")):
            self.mode_selector.set_active(index)
            if self.mode != expected:
                raise RuntimeError(f"Mode control did not select {expected}")
        foreground_voxel = tuple(int(value) for value in np.argwhere(self.pair.label != 0)[0])
        axial = next(plane for plane in self.planes if plane.name == "Axial")
        self.slice_sliders[axial.name].set_val(foreground_voxel[axial.slice_axis])
        self._on_click(SimpleNamespace(
            inaxes=self.axes[axial.name],
            xdata=float(foreground_voxel[axial.horizontal_axis]),
            ydata=float(foreground_voxel[axial.vertical_axis]),
        ))
        clicked_id = int(round(float(self.pair.label[foreground_voxel])))
        if f"ID {clicked_id}:" not in self.label_status.get_text():
            raise RuntimeError("Label ID/region click display did not update")
        for plane in self.planes:
            self.slice_sliders[plane.name].set_val(self.initial_slices[plane.slice_axis])
        self.opacity_slider.set_val(0.45)
        self.mode_selector.set_active(2)
        transparent = self.label_cmap(0)[3] == 0.0
        colors_unique = len({self.label_cmap(index) for index in range(1, len(self._label_ids))}) == len(self._label_ids) - 1
        if not transparent or not colors_unique:
            raise RuntimeError("Label transparency or deterministic color assignment failed")
        return {
            "slice_controls": "passed",
            "opacity_control": "passed",
            "display_modes": "passed",
            "label_id_region_display": "passed",
            "background_transparency": "passed",
            "foreground_color_uniqueness": "passed",
        }

    def save_combined(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.figure.savefig(path, dpi=150, facecolor=self.figure.get_facecolor())

    def save_plane(self, plane: Plane, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        index = self.initial_slices[plane.slice_axis]
        figure, axis = plt.subplots(figsize=(7, 7), facecolor="#101318")
        axis.set_facecolor("#07090c")
        axis.imshow(
            _slice(self.pair.mri, plane, index), cmap="gray", origin="lower", interpolation="nearest",
            vmin=self.mri_vmin, vmax=self.mri_vmax,
        )
        axis.imshow(
            _slice(self._label_index_volume, plane, index), cmap=self.label_cmap, origin="lower",
            interpolation="nearest", vmin=0, vmax=len(self._label_ids) - 1, alpha=0.45,
        )
        axis.set_xticks([])
        axis.set_yticks([])
        self._decorate_axis(axis, plane, index)
        figure.suptitle(
            f"{self.pair.record.participant_id} | {self.pair.record.cohort} | {self.pair.record.space} | "
            f"orientation {''.join(self.pair.orientation)}\n"
            "Manual DKT31 reference overlay — not a model prediction",
            color="white",
            fontsize=12,
        )
        figure.tight_layout(rect=(0, 0, 1, 0.92))
        figure.savefig(path, dpi=150, facecolor=figure.get_facecolor())
        plt.close(figure)

    def close(self) -> None:
        plt.close(self.figure)
