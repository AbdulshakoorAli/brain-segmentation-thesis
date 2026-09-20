"""Read-only path, gzip, NiBabel, and loader audit for all canonical pairs."""

from __future__ import annotations

import csv
import gzip
import hashlib
import json
import os
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import nibabel as nib  # noqa: E402
import numpy as np  # noqa: E402

from brain_segmentation.loading import load_verified_pair, load_verified_records  # noqa: E402

MANIFEST = ROOT / "data/derived/manifests/mindboggle101_scan_manifest.csv"
DICTIONARY = ROOT / "data/derived/dictionaries/dkt_label_dictionary.csv"
OUTPUT = ROOT / "data/derived/qc/mindboggle101_nifti_readability_audit.csv"

FIELDS = (
    "canonical_pair_id", "cohort", "subject", "space", "file_role", "manifest_path",
    "manifest_value_repr", "leading_whitespace", "trailing_whitespace", "invisible_characters",
    "resolved_absolute_path", "inside_expected_data_directory", "exists", "is_regular_file",
    "readable", "file_size_bytes", "gzip_signature", "gzip_decompression_crc", "decompressed_bytes",
    "sha256", "accepted_qc_sha256", "accepted_hash_match", "nibabel_header_load", "shape",
    "affine_access", "voxel_array_load", "finite_voxels", "failure_stage", "exception_type",
    "exception_message", "loader_pair_result", "audit_status",
)


def yes(value: bool) -> str:
    return "passed" if value else "failed"


def invisible(value: str) -> str:
    return ";".join(f"U+{ord(character):04X}@{index}" for index, character in enumerate(value) if (
        character.isspace() and character != " " or ord(character) < 32 or ord(character) == 127
    ))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def qc_hashes() -> dict[tuple[str, str], str]:
    result = {}
    for cohort_file in (
        "extra18_pair_qc.csv", "mmrr21_pair_qc.csv", "nki_rs22_pair_qc.csv",
        "nki_trt20_pair_qc.csv", "oasis_trt20_pair_qc.csv",
    ):
        path = ROOT / "data/derived/qc" / cohort_file
        with path.open(newline="", encoding="utf-8-sig") as stream:
            for row in csv.DictReader(stream):
                result[(row["scan_id"], "mri")] = row["mri_file_sha256"]
                result[(row["scan_id"], "label")] = row["label_file_sha256"]
    return result


def audit_file(record, role: str, relative: str, expected_hash: str) -> dict[str, str]:
    row = {field: "" for field in FIELDS}
    row.update({"canonical_pair_id": record.canonical_pair_id, "cohort": record.cohort,
                "subject": record.participant_id, "space": record.space, "file_role": role,
                "manifest_path": relative, "manifest_value_repr": repr(relative),
                "leading_whitespace": yes(relative == relative.lstrip()),
                "trailing_whitespace": yes(relative == relative.rstrip()),
                "invisible_characters": invisible(relative), "accepted_qc_sha256": expected_hash})
    expected_root = (ROOT / "data/raw/mindboggle101/extracted").resolve()
    try:
        candidate = Path(relative)
        if candidate.is_absolute():
            raise ValueError("manifest path is absolute")
        resolved = (ROOT / candidate).resolve()
        row["resolved_absolute_path"] = str(resolved)
        try:
            resolved.relative_to(expected_root); inside = True
        except ValueError:
            inside = False
        row["inside_expected_data_directory"] = yes(inside)
        if not inside:
            raise ValueError("resolved path leaves expected extracted-data directory")
    except Exception as exc:
        row.update(failure_stage="path resolution", exception_type=type(exc).__name__, exception_message=str(exc), audit_status="failed")
        return row
    row["exists"] = yes(resolved.exists())
    if not resolved.exists():
        row.update(failure_stage="file open", exception_type="FileNotFoundError", exception_message="resolved file does not exist", audit_status="failed")
        return row
    row["is_regular_file"] = yes(resolved.is_file())
    if not resolved.is_file():
        row.update(failure_stage="file open", exception_type="IsADirectoryError", exception_message="resolved path is not a regular file", audit_status="failed")
        return row
    try:
        size = resolved.stat().st_size
        with resolved.open("rb") as stream:
            signature = stream.read(2)
        row.update(readable="passed", file_size_bytes=str(size), gzip_signature=yes(signature == b"\x1f\x8b"), sha256=sha256(resolved))
        row["accepted_hash_match"] = yes(bool(expected_hash) and row["sha256"] == expected_hash)
        if signature != b"\x1f\x8b":
            raise gzip.BadGzipFile(f"signature is {signature.hex()}, expected 1f8b")
    except Exception as exc:
        row.update(failure_stage="file open", exception_type=type(exc).__name__, exception_message=str(exc), audit_status="failed")
        return row
    try:
        decompressed = 0
        with gzip.open(resolved, "rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                decompressed += len(block)
        row.update(gzip_decompression_crc="passed", decompressed_bytes=str(decompressed))
    except Exception as exc:
        row.update(gzip_decompression_crc="failed", failure_stage="gzip decompression", exception_type=type(exc).__name__, exception_message=str(exc), audit_status="failed")
        return row
    try:
        image = nib.load(str(resolved)); row["nibabel_header_load"] = "passed"; row["shape"] = "x".join(map(str, image.shape))
    except Exception as exc:
        row.update(nibabel_header_load="failed", failure_stage="NIfTI header parsing", exception_type=type(exc).__name__, exception_message=str(exc), audit_status="failed")
        return row
    try:
        affine = np.asarray(image.affine); _ = affine[3, 3]; row["affine_access"] = yes(affine.shape == (4, 4) and np.all(np.isfinite(affine)))
    except Exception as exc:
        row.update(affine_access="failed", failure_stage="NIfTI header parsing", exception_type=type(exc).__name__, exception_message=str(exc), audit_status="failed")
        return row
    try:
        array = np.asanyarray(image.dataobj); row["voxel_array_load"] = yes(array.shape == image.shape); row["finite_voxels"] = yes(bool(np.all(np.isfinite(array))))
        if row["voxel_array_load"] != "passed" or row["finite_voxels"] != "passed":
            raise ValueError("voxel array shape or finiteness check failed")
    except Exception as exc:
        row.update(voxel_array_load="failed", failure_stage="voxel-data reading", exception_type=type(exc).__name__, exception_message=str(exc), audit_status="failed")
        return row
    row["audit_status"] = "passed" if row["accepted_hash_match"] == "passed" else "failed"
    if row["audit_status"] == "failed":
        row.update(failure_stage="accepted hash comparison", exception_type="HashMismatch", exception_message="current file SHA-256 differs from accepted QC")
    return row


def main() -> None:
    started = time.perf_counter(); records = load_verified_records(MANIFEST); accepted = qc_hashes(); rows=[]; loader_results={}
    for index, record in enumerate(records, start=1):
        pair_rows = [
            audit_file(record, "mri", record.mri_path, accepted.get((record.scan_id, "mri"), "")),
            audit_file(record, "label", record.label_path, accepted.get((record.scan_id, "label"), "")),
        ]
        try:
            pair = load_verified_pair(ROOT, record, DICTIONARY)
            loader_result = "passed" if all(value == "passed" for value in pair.validation.values()) else "failed"
        except Exception as exc:
            loader_result = f"failed:{type(exc).__name__}:{exc}"
        loader_results[record.canonical_pair_id] = loader_result
        for row in pair_rows:
            row["loader_pair_result"] = loader_result; rows.append(row)
        if index % 20 == 0 or index == len(records):
            print(f"audited_pairs={index}/{len(records)}", flush=True)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS, lineterminator="\n"); writer.writeheader(); writer.writerows(rows)
    failed=[row for row in rows if row["audit_status"] != "passed"]
    print(json.dumps({"records":len(records),"files":len(rows),"passed_files":len(rows)-len(failed),"failed_files":len(failed),"loader_failures":sum(not value.startswith("passed") for value in loader_results.values()),"failure_stages":Counter(row["failure_stage"] for row in failed),"seconds":round(time.perf_counter()-started,3)},default=dict,sort_keys=True))


if __name__ == "__main__":
    main()

