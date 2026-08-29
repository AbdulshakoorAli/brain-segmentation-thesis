"""Run the accepted reusable QC implementation on MMRR-21 candidates."""

from __future__ import annotations

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
)


MANIFEST_PATH = REPO_ROOT / "data/derived/manifests/mmrr21_scan_inventory.csv"
DICTIONARY_PATH = REPO_ROOT / "data/derived/dictionaries/dkt_label_dictionary.csv"
QC_PATH = REPO_ROOT / "data/derived/qc/mmrr21_pair_qc.csv"
FAILURES_PATH = REPO_ROOT / "data/derived/qc/mmrr21_failures.csv"


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        return list(reader.fieldnames or []), list(reader)


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def ordered_fields(rows: list[dict[str, str]], preferred: list[str]) -> list[str]:
    all_fields = {field for row in rows for field in row}
    return preferred + sorted(all_fields - set(preferred))


def main() -> int:
    manifest_fields, manifest_rows = read_csv(MANIFEST_PATH)
    if len(manifest_rows) != 42 or {row["cohort"] for row in manifest_rows} != {"MMRR-21"}:
        raise ValueError("Expected exactly 42 MMRR-21 manifest rows")
    if sum(row["space"] == "native" for row in manifest_rows) != 21:
        raise ValueError("Expected exactly 21 native rows")
    if sum(row["space"] == "MNI152" for row in manifest_rows) != 21:
        raise ValueError("Expected exactly 21 MNI152 rows")
    if len({row["scan_id"] for row in manifest_rows}) != 42:
        raise ValueError("Manifest scan IDs are not unique")
    if any("manual+aseg" in row["label_path"] for row in manifest_rows):
        raise ValueError("Auxiliary manual+aseg selected as canonical")

    _, dictionary_rows = read_csv(DICTIONARY_PATH)
    known_label_ids = {int(row["original_label_id"]) for row in dictionary_rows}
    if len(dictionary_rows) != 62 or len(known_label_ids) != 62:
        raise ValueError("Existing DKT dictionary is not the accepted 62-row dictionary")

    qc_rows: list[dict[str, str]] = []
    for source in manifest_rows:
        outcome = evaluate_pair(
            REPO_ROOT / source["mri_path"],
            REPO_ROOT / source["label_path"],
            source["space"],
            known_label_ids,
        )
        qc_rows.append(
            {
                "scan_id": source["scan_id"],
                "participant_id": source["participant_id"],
                "cohort": source["cohort"],
                "space": source["space"],
                "mri_path": source["mri_path"],
                "label_path": source["label_path"],
                **outcome,
            }
        )
    annotate_duplicates(qc_rows)
    for row in qc_rows:
        finalize_status(row)

    preferred = [
        "scan_id", "participant_id", "cohort", "space", "mri_path", "label_path",
        "validation_status", "failed_checks", "blocked_checks", *REQUIRED_CHECK_COLUMNS,
    ]
    write_csv(QC_PATH, ordered_fields(qc_rows, preferred), qc_rows)

    failures: list[dict[str, str]] = []
    for row in qc_rows:
        for check in REQUIRED_CHECK_COLUMNS:
            if row.get(check) in {"failed", "blocked"}:
                failures.append(
                    {
                        "scan_id": row["scan_id"],
                        "participant_id": row["participant_id"],
                        "space": row["space"],
                        "check": check,
                        "status": row[check],
                        "detail": row.get(check.removesuffix("_status") + "_error", ""),
                        "unknown_label_ids": row.get("unknown_label_ids", ""),
                    }
                )
    write_csv(
        FAILURES_PATH,
        ["scan_id", "participant_id", "space", "check", "status", "detail", "unknown_label_ids"],
        failures,
    )

    qc_by_scan = {row["scan_id"]: row for row in qc_rows}
    derived_fields = [
        "mri_dimensions", "label_dimensions", "mri_voxel_spacing", "label_voxel_spacing",
        "mri_orientation", "label_orientation", "affine_match", "label_ids_present",
        "unknown_label_ids", "validation_status",
    ]
    output_fields = manifest_fields + [field for field in derived_fields if field not in manifest_fields]
    updated_rows: list[dict[str, str]] = []
    for source in manifest_rows:
        qc = qc_by_scan[source["scan_id"]]
        updated = dict(source)
        updated.update(
            {
                "pairing_status": qc["validation_status"],
                "exclusion_reason": qc["failed_checks"] or qc["blocked_checks"],
                "mri_dimensions": qc.get("mri_dimensions", ""),
                "label_dimensions": qc.get("label_dimensions", ""),
                "mri_voxel_spacing": qc.get("mri_voxel_spacing", ""),
                "label_voxel_spacing": qc.get("label_voxel_spacing", ""),
                "mri_orientation": qc.get("mri_orientation", ""),
                "label_orientation": qc.get("label_orientation", ""),
                "affine_match": qc.get("affine_status", ""),
                "label_ids_present": qc.get("label_ids", ""),
                "unknown_label_ids": qc.get("unknown_label_ids", ""),
                "validation_status": qc["validation_status"],
            }
        )
        updated_rows.append(updated)
    write_csv(MANIFEST_PATH, output_fields, updated_rows)

    verified = sum(row["validation_status"] == "verified" for row in qc_rows)
    failed = sum(row["validation_status"] == "failed" for row in qc_rows)
    blocked = sum(row["validation_status"] == "blocked" for row in qc_rows)
    unknown = sorted(
        {int(item) for row in qc_rows for item in row.get("unknown_label_ids", "").split(";") if item}
    )
    print(f"pairs={len(qc_rows)} verified={verified} failed={failed} blocked={blocked}")
    print(f"failure_rows={len(failures)} unknown_label_ids={';'.join(map(str, unknown))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

