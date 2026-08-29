"""Validate and render the deterministic Extra-18 visualization pre-MVP."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / "data/derived/cache/matplotlib"))
if "--show" not in sys.argv:
    os.environ.setdefault("MPLBACKEND", "Agg")

if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from brain_segmentation.loading import load_verified_pair, select_verified_record
from brain_segmentation.qc import AFFINE_ATOL, AFFINE_RTOL
from brain_segmentation.visualization import OrthogonalDKTViewer


MANIFEST = ROOT / "data/derived/manifests/mindboggle101_scan_manifest.csv"
DICTIONARY = ROOT / "data/derived/dictionaries/dkt_label_dictionary.csv"
OUTPUT_DIR = ROOT / "reports/phase1a/screenshots/extra18_visualization"
VALIDATION_OUT = ROOT / "data/derived/qc/extra18_visualization_validation.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--show", action="store_true", help="Open the interactive viewer after saving screenshots")
    args = parser.parse_args()

    record = select_verified_record(MANIFEST, cohort="Extra-18", space="native")
    mri_path = ROOT / record.mri_path
    label_path = ROOT / record.label_path
    raw_before = {"mri": sha256(mri_path), "label": sha256(label_path)}
    pair = load_verified_pair(ROOT, record, DICTIONARY)
    viewer = OrthogonalDKTViewer(pair)
    control_checks = viewer.exercise_controls()

    screenshot_paths: list[Path] = []
    for plane in viewer.planes:
        path = OUTPUT_DIR / f"afterthought1_native_{plane.name.lower()}_overlay.png"
        viewer.save_plane(plane, path)
        screenshot_paths.append(path)
    combined_path = OUTPUT_DIR / "afterthought1_native_three_plane_overlay.png"
    viewer.save_combined(combined_path)
    screenshot_paths.append(combined_path)
    if any(not path.is_file() or path.stat().st_size == 0 for path in screenshot_paths):
        raise RuntimeError("One or more screenshots were not created")

    raw_after = {"mri": sha256(mri_path), "label": sha256(label_path)}
    if raw_before != raw_after:
        raise RuntimeError("A selected raw NIfTI checksum changed")
    affine_difference = float(abs(pair.affine - pair.label_affine).max())
    validation = {
        "selection_rule": "minimum (canonical_pair_id, scan_id) among verified included Extra-18 native rows",
        "canonical_pair_id": record.canonical_pair_id,
        "scan_id": record.scan_id,
        "participant_id": record.participant_id,
        "participant_group_id": record.participant_group_id,
        "source_subject_id": record.source_subject_id,
        "source_participant_identifier": record.source_participant_identifier,
        "cohort": record.cohort,
        "space": record.space,
        "mri_path": record.mri_path,
        "label_path": record.label_path,
        "shape": list(pair.mri.shape),
        "spacing": list(pair.spacing),
        "orientation": list(pair.orientation),
        "mri_affine": pair.affine.tolist(),
        "label_affine": pair.label_affine.tolist(),
        "affine_max_abs_difference": affine_difference,
        "affine_rtol": AFFINE_RTOL,
        "affine_atol": AFFINE_ATOL,
        "observed_label_ids": list(pair.observed_label_ids),
        "initial_slices": list(viewer.initial_slices),
        "pair_validation": pair.validation,
        "render_validation": {
            "axial_render": "passed",
            "coronal_render": "passed",
            "sagittal_render": "passed",
            **control_checks,
        },
        "screenshots": [str(path.relative_to(ROOT)).replace("\\", "/") for path in screenshot_paths],
        "raw_sha256_before": raw_before,
        "raw_sha256_after": raw_after,
        "raw_preservation": "passed",
        "reference_notice": "Manual DKT31 reference segmentation; not a model prediction.",
    }
    VALIDATION_OUT.parent.mkdir(parents=True, exist_ok=True)
    VALIDATION_OUT.write_text(json.dumps(validation, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "canonical_pair_id": record.canonical_pair_id,
        "shape": list(pair.mri.shape),
        "spacing": list(pair.spacing),
        "orientation": list(pair.orientation),
        "initial_slices": list(viewer.initial_slices),
        "validation_checks": len(pair.validation),
        "screenshots": len(screenshot_paths),
        "raw_preservation": "passed",
    }, sort_keys=True))
    if args.show:
        import matplotlib.pyplot as plt
        plt.show()
    else:
        viewer.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
