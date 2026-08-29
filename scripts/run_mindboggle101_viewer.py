"""Manifest-driven selector and smoke validator for verified Mindboggle-101 pairs."""

from __future__ import annotations

import argparse
import gc
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / "data/derived/cache/matplotlib"))
if "--smoke-validate" in sys.argv:
    os.environ.setdefault("MPLBACKEND", "Agg")
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from brain_segmentation.loading import (
    CanonicalPairRecord,
    get_record_by_canonical_pair_id,
    load_verified_pair,
    load_verified_records,
)
from brain_segmentation.qc import sha256_file
from brain_segmentation.visualization import OrthogonalDKTViewer


MANIFEST = ROOT / "data/derived/manifests/mindboggle101_scan_manifest.csv"
DICTIONARY = ROOT / "data/derived/dictionaries/dkt_label_dictionary.csv"
SMOKE_OUT = ROOT / "data/derived/qc/mindboggle101_viewer_smoke_validation.json"


def filtered_records(
    records: tuple[CanonicalPairRecord, ...],
    *,
    cohort: str | None = None,
    participant_id: str | None = None,
    space: str | None = None,
) -> tuple[CanonicalPairRecord, ...]:
    """Filter the catalog without assuming subject names, paths, or dimensions."""
    return tuple(
        record
        for record in records
        if (cohort is None or record.cohort == cohort)
        and (participant_id is None or record.participant_id == participant_id)
        and (space is None or record.space == space)
    )


def deterministic_smoke_records(
    records: tuple[CanonicalPairRecord, ...],
) -> tuple[CanonicalPairRecord, ...]:
    """Select one stable native and MNI152 record from every observed cohort."""
    selected: list[CanonicalPairRecord] = []
    cohorts = sorted({record.cohort for record in records})
    for cohort in cohorts:
        cohort_records = filtered_records(records, cohort=cohort)
        spaces = {record.space for record in cohort_records}
        if spaces != {"native", "MNI152"}:
            raise ValueError(f"Cohort {cohort} does not have exactly native and MNI152 products: {sorted(spaces)}")
        for space in ("native", "MNI152"):
            candidates = filtered_records(cohort_records, space=space)
            selected.append(min(candidates, key=lambda record: (record.canonical_pair_id, record.scan_id)))
    expected = len(cohorts) * 2
    if len(selected) != expected:
        raise ValueError(f"Expected {expected} smoke records, selected {len(selected)}")
    return tuple(selected)


def load_viewer(record: CanonicalPairRecord) -> tuple[object, OrthogonalDKTViewer]:
    """Run essential checks and construct the viewer for one manifest record."""
    pair = load_verified_pair(ROOT, record, DICTIONARY)
    viewer = OrthogonalDKTViewer(pair)
    return pair, viewer


def smoke_validate(records: tuple[CanonicalPairRecord, ...]) -> int:
    selected = deterministic_smoke_records(records)
    results: list[dict[str, object]] = []
    for record in selected:
        result: dict[str, object] = {
            "canonical_pair_id": record.canonical_pair_id,
            "scan_id": record.scan_id,
            "participant_id": record.participant_id,
            "cohort": record.cohort,
            "space": record.space,
            "status": "failed",
            "error": "",
        }
        mri_path = ROOT / record.mri_path
        label_path = ROOT / record.label_path
        hashes_before = {"mri": sha256_file(mri_path), "label": sha256_file(label_path)}
        viewer = None
        pair = None
        try:
            pair, viewer = load_viewer(record)
            viewer.figure.canvas.draw()
            if set(viewer.axes) != {"Axial", "Coronal", "Sagittal"}:
                raise RuntimeError("Viewer did not construct all three anatomical planes")
            if any(viewer.mri_artists[name].get_array().ndim != 2 for name in viewer.axes):
                raise RuntimeError("A rendered MRI plane is not two-dimensional")
            if any(viewer.label_artists[name].get_array().ndim != 2 for name in viewer.axes):
                raise RuntimeError("A rendered label plane is not two-dimensional")
            controls = viewer.exercise_controls()
            hashes_after = {"mri": sha256_file(mri_path), "label": sha256_file(label_path)}
            if hashes_before != hashes_after:
                raise RuntimeError("Selected raw file checksum changed")
            result.update({
                "status": "passed",
                "shape": list(pair.mri.shape),
                "spacing": list(pair.spacing),
                "orientation": "".join(pair.orientation),
                "plane_axes": {
                    plane.name: {
                        "slice_axis": plane.slice_axis,
                        "horizontal_axis": plane.horizontal_axis,
                        "vertical_axis": plane.vertical_axis,
                    }
                    for plane in viewer.planes
                },
                "essential_checks": pair.validation,
                "render_checks": {
                    "axial": "passed",
                    "coronal": "passed",
                    "sagittal": "passed",
                    **controls,
                },
                "raw_sha256_before": hashes_before,
                "raw_sha256_after": hashes_after,
            })
            print(f"PASSED {record.cohort} {record.space} {record.canonical_pair_id}", flush=True)
        except Exception as exc:
            result["error"] = f"{type(exc).__name__}: {exc}"
            print(f"FAILED {record.cohort} {record.space}: {result['error']}", flush=True)
        finally:
            if viewer is not None:
                viewer.close()
            del viewer, pair
            gc.collect()
        results.append(result)

    payload = {
        "selection_rule": "minimum (canonical_pair_id, scan_id) for each observed cohort and each required space",
        "manifest_verified_record_count": len(records),
        "observed_cohorts": sorted({record.cohort for record in records}),
        "selected_record_count": len(selected),
        "passed": sum(result["status"] == "passed" for result in results),
        "failed": sum(result["status"] == "failed" for result in results),
        "records": results,
        "screenshots_created": 0,
        "reference_notice": "Displayed labels are manual DKT31 references, not model predictions.",
    }
    SMOKE_OUT.parent.mkdir(parents=True, exist_ok=True)
    SMOKE_OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({key: payload[key] for key in ("manifest_verified_record_count", "selected_record_count", "passed", "failed")}, sort_keys=True))
    return 0 if payload["failed"] == 0 else 1


def launch_selector(records: tuple[CanonicalPairRecord, ...]) -> int:
    """Launch cascading manifest selectors; record errors remain in the selector window."""
    import tkinter as tk
    from tkinter import ttk

    import matplotlib.pyplot as plt

    root = tk.Tk()
    root.title("Mindboggle-101 verified manual-DKT31 viewer")
    root.geometry("1060x430")
    root.columnconfigure(1, weight=1)

    cohort_var = tk.StringVar()
    participant_var = tk.StringVar()
    space_var = tk.StringVar()
    pair_var = tk.StringVar()
    preview_var = tk.StringVar()
    status_var = tk.StringVar(value=f"Ready: {len(records)} verified canonical pairs")
    active_viewer: list[OrthogonalDKTViewer | None] = [None]

    ttk.Label(root, text="Cohort").grid(row=0, column=0, sticky="w", padx=12, pady=8)
    cohort_box = ttk.Combobox(root, textvariable=cohort_var, state="readonly")
    cohort_box.grid(row=0, column=1, sticky="ew", padx=12, pady=8)
    ttk.Label(root, text="Participant / scan").grid(row=1, column=0, sticky="w", padx=12, pady=8)
    participant_box = ttk.Combobox(root, textvariable=participant_var, state="readonly")
    participant_box.grid(row=1, column=1, sticky="ew", padx=12, pady=8)
    ttk.Label(root, text="Coordinate space").grid(row=2, column=0, sticky="w", padx=12, pady=8)
    space_box = ttk.Combobox(root, textvariable=space_var, state="readonly")
    space_box.grid(row=2, column=1, sticky="ew", padx=12, pady=8)
    ttk.Label(root, text="Canonical pair").grid(row=3, column=0, sticky="w", padx=12, pady=8)
    pair_box = ttk.Combobox(root, textvariable=pair_var, state="readonly")
    pair_box.grid(row=3, column=1, sticky="ew", padx=12, pady=8)
    ttk.Label(root, textvariable=preview_var, wraplength=1000, justify="left").grid(
        row=4, column=0, columnspan=2, sticky="w", padx=12, pady=12
    )
    status_label = tk.Label(root, textvariable=status_var, wraplength=1000, justify="left", anchor="w")
    status_label.grid(row=6, column=0, columnspan=2, sticky="w", padx=12, pady=12)

    def set_values(box, variable, values: list[str]) -> None:
        box["values"] = values
        variable.set(values[0] if values else "")

    def refresh_preview(*_args) -> None:
        if not pair_var.get():
            preview_var.set("")
            return
        record = get_record_by_canonical_pair_id(records, pair_var.get())
        preview_var.set(
            f"scan_id: {record.scan_id}\nshape: {record.mri_dimensions} | spacing: {record.mri_voxel_spacing} mm | "
            f"orientation: {record.mri_orientation}\nManual DKT31 reference segmentation — not a model prediction."
        )

    def refresh_pairs(*_args) -> None:
        candidates = filtered_records(
            records, cohort=cohort_var.get(), participant_id=participant_var.get(), space=space_var.get()
        )
        set_values(pair_box, pair_var, sorted(record.canonical_pair_id for record in candidates))
        refresh_preview()

    def refresh_spaces(*_args) -> None:
        candidates = filtered_records(records, cohort=cohort_var.get(), participant_id=participant_var.get())
        set_values(space_box, space_var, sorted({record.space for record in candidates}))
        refresh_pairs()

    def refresh_participants(*_args) -> None:
        candidates = filtered_records(records, cohort=cohort_var.get())
        set_values(participant_box, participant_var, sorted({record.participant_id for record in candidates}))
        refresh_spaces()

    def open_selected() -> None:
        try:
            record = get_record_by_canonical_pair_id(records, pair_var.get())
            pair, viewer = load_viewer(record)
            viewer.figure.canvas.draw()
            if active_viewer[0] is not None:
                active_viewer[0].close()
            active_viewer[0] = viewer
            status_var.set(
                f"Loaded {record.canonical_pair_id}: shape {pair.mri.shape}, spacing {pair.spacing}, "
                f"orientation {''.join(pair.orientation)}. All essential checks passed."
            )
            status_label.configure(foreground="#176b2c")
            plt.show(block=False)
        except Exception as exc:
            status_var.set(f"Could not load selected record: {type(exc).__name__}: {exc}")
            status_label.configure(foreground="#a11a1a")

    ttk.Button(root, text="Load selected verified pair", command=open_selected).grid(
        row=5, column=0, columnspan=2, pady=8
    )
    cohort_box.bind("<<ComboboxSelected>>", refresh_participants)
    participant_box.bind("<<ComboboxSelected>>", refresh_spaces)
    space_box.bind("<<ComboboxSelected>>", refresh_pairs)
    pair_box.bind("<<ComboboxSelected>>", refresh_preview)
    set_values(cohort_box, cohort_var, sorted({record.cohort for record in records}))
    refresh_participants()
    root.mainloop()
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--canonical-pair-id", help="Open one verified canonical pair directly")
    parser.add_argument("--smoke-validate", action="store_true", help="Validate exactly one native and MNI152 pair per cohort")
    args = parser.parse_args()
    records = load_verified_records(MANIFEST)
    if args.smoke_validate:
        return smoke_validate(records)
    if args.canonical_pair_id:
        try:
            record = get_record_by_canonical_pair_id(records, args.canonical_pair_id)
            _pair, viewer = load_viewer(record)
        except Exception as exc:
            print(f"Could not load selected record: {type(exc).__name__}: {exc}", file=sys.stderr)
            return 2
        import matplotlib.pyplot as plt
        plt.show()
        viewer.close()
        return 0
    return launch_selector(records)


if __name__ == "__main__":
    raise SystemExit(main())
