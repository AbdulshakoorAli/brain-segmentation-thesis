"""Run deterministic QC only for the 36 Extra-18 canonical candidate pairs."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from brain_segmentation.qc import (  # noqa: E402
    REQUIRED_CHECK_COLUMNS,
    annotate_duplicates,
    evaluate_pair,
    finalize_status,
    parse_dkt_cortical_definitions,
)


MANIFEST_PATH = REPO_ROOT / "data/derived/manifests/extra18_scan_inventory.csv"
LABEL_DEFINITIONS_PATH = REPO_ROOT / "data/raw/mindboggle101/metadata/label_definitions.txt"
QC_PATH = REPO_ROOT / "data/derived/qc/extra18_pair_qc.csv"
FAILURES_PATH = REPO_ROOT / "data/derived/qc/extra18_failures.csv"
DICTIONARY_PATH = REPO_ROOT / "data/derived/dictionaries/dkt_label_dictionary.csv"


def read_manifest(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        rows = list(reader)
        fields = list(reader.fieldnames or [])
    if len(rows) != 36:
        raise ValueError(f"Expected exactly 36 Extra-18 rows, found {len(rows)}")
    if {row["cohort"] for row in rows} != {"Extra-18"}:
        raise ValueError("Manifest includes a cohort other than Extra-18")
    if sum(row["space"] == "native" for row in rows) != 18:
        raise ValueError("Manifest does not contain exactly 18 native rows")
    if sum(row["space"] == "MNI152" for row in rows) != 18:
        raise ValueError("Manifest does not contain exactly 18 MNI152 rows")
    if len({row["scan_id"] for row in rows}) != 36:
        raise ValueError("Manifest scan_id values are not unique")
    for row in rows:
        if "manual+aseg" in row["label_path"]:
            raise ValueError(f"Auxiliary manual+aseg selected as canonical: {row['scan_id']}")
        if Path(row["mri_path"]).name not in {
            "t1weighted_brain.nii.gz",
            "t1weighted_brain.MNI152.nii.gz",
        }:
            raise ValueError(f"Noncanonical MRI selected: {row['scan_id']}")
        if Path(row["label_path"]).name not in {
            "labels.DKT31.manual.nii.gz",
            "labels.DKT31.manual.MNI152.nii.gz",
        }:
            raise ValueError(f"Noncanonical label selected: {row['scan_id']}")
    return fields, rows


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames, lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def ordered_fields(rows: list[dict[str, str]], preferred: list[str]) -> list[str]:
    all_fields = {field for row in rows for field in row}
    return preferred + sorted(all_fields - set(preferred))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    arguments = parser.parse_args()

    manifest_fields, manifest_rows = read_manifest(arguments.manifest)
    dictionary_rows = parse_dkt_cortical_definitions(LABEL_DEFINITIONS_PATH)
    known_label_ids = {int(row["original_label_id"]) for row in dictionary_rows}

    qc_rows: list[dict[str, str]] = []
    for source_row in manifest_rows:
        mri_path = REPO_ROOT / source_row["mri_path"]
        label_path = REPO_ROOT / source_row["label_path"]
        outcome = evaluate_pair(mri_path, label_path, source_row["space"], known_label_ids)
        qc_rows.append(
            {
                "scan_id": source_row["scan_id"],
                "participant_id": source_row["participant_id"],
                "cohort": source_row["cohort"],
                "space": source_row["space"],
                "mri_path": source_row["mri_path"],
                "label_path": source_row["label_path"],
                **outcome,
            }
        )

    annotate_duplicates(qc_rows)
    for row in qc_rows:
        finalize_status(row)

    qc_preferred = [
        "scan_id", "participant_id", "cohort", "space", "mri_path", "label_path",
        "validation_status", "failed_checks", "blocked_checks", *REQUIRED_CHECK_COLUMNS,
    ]
    qc_fields = ordered_fields(qc_rows, qc_preferred)
    write_csv(QC_PATH, qc_fields, qc_rows)

    failure_rows: list[dict[str, str]] = []
    for row in qc_rows:
        for check in REQUIRED_CHECK_COLUMNS:
            if row.get(check) in {"failed", "blocked"}:
                failure_rows.append(
                    {
                        "scan_id": row["scan_id"],
                        "participant_id": row["participant_id"],
                        "space": row["space"],
                        "check": check,
                        "status": row[check],
                        "detail": row.get(check.removesuffix("_status") + "_error", ""),
                    }
                )
    write_csv(
        FAILURES_PATH,
        ["scan_id", "participant_id", "space", "check", "status", "detail"],
        failure_rows,
    )
    write_csv(
        DICTIONARY_PATH,
        ["original_label_id", "region_name", "hemisphere", "class_index", "source_reference"],
        dictionary_rows,
    )

    qc_by_scan = {row["scan_id"]: row for row in qc_rows}
    derived_manifest_fields = [
        "mri_dimensions", "label_dimensions", "mri_voxel_spacing", "label_voxel_spacing",
        "mri_orientation", "label_orientation", "affine_match", "label_ids_present",
        "unknown_label_ids", "validation_status",
    ]
    output_manifest_fields = manifest_fields + [
        field for field in derived_manifest_fields if field not in manifest_fields
    ]
    updated_manifest: list[dict[str, str]] = []
    for source_row in manifest_rows:
        qc = qc_by_scan[source_row["scan_id"]]
        status = qc["validation_status"]
        updated = dict(source_row)
        updated.update(
            {
                "pairing_status": status,
                "exclusion_reason": qc["failed_checks"] or qc["blocked_checks"],
                "notes": (
                    "Canonical skull-stripped T1/manual DKT31 pair; manual+aseg remains auxiliary. "
                    "Header and voxel QC performed without modifying source files."
                ),
                "mri_dimensions": qc.get("mri_dimensions", ""),
                "label_dimensions": qc.get("label_dimensions", ""),
                "mri_voxel_spacing": qc.get("mri_voxel_spacing", ""),
                "label_voxel_spacing": qc.get("label_voxel_spacing", ""),
                "mri_orientation": qc.get("mri_orientation", ""),
                "label_orientation": qc.get("label_orientation", ""),
                "affine_match": qc.get("affine_status", ""),
                "label_ids_present": qc.get("label_ids", ""),
                "unknown_label_ids": qc.get("unknown_label_ids", ""),
                "validation_status": status,
            }
        )
        updated_manifest.append(updated)
    write_csv(arguments.manifest, output_manifest_fields, updated_manifest)

    verified = sum(row["validation_status"] == "verified" for row in qc_rows)
    failed = sum(row["validation_status"] == "failed" for row in qc_rows)
    blocked = sum(row["validation_status"] == "blocked" for row in qc_rows)
    print(f"pairs={len(qc_rows)} verified={verified} failed={failed} blocked={blocked}")
    print(f"dictionary_rows={len(dictionary_rows)} failure_rows={len(failure_rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
