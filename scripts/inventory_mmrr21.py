"""Validate the extracted MMRR-21 tree and build its canonical-pair manifest."""

from __future__ import annotations

import csv
import re
import tarfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
ARCHIVE_PATH = REPO_ROOT / "data/raw/mindboggle101/archives/volumes/MMRR-21_volumes.tar.gz"
EXTRACT_TARGET = REPO_ROOT / "data/raw/mindboggle101/extracted/MMRR-21"
VOLUME_ROOT = EXTRACT_TARGET / "MMRR-21_volumes"
SUBJECT_LIST_PATH = REPO_ROOT / "data/raw/mindboggle101/metadata/subject_list_Mindboggle101.txt"
SUBJECT_SOURCES_PATH = REPO_ROOT / "data/raw/mindboggle101/metadata/subject_sources_Mindboggle101.txt"
SCAN_INFO_ARCHIVE = (
    REPO_ROOT
    / "data/raw/mindboggle101/archives/scan-information/subject_scans_info_Mindboggle101.tar.gz"
)
MANIFEST_PATH = REPO_ROOT / "data/derived/manifests/mmrr21_scan_inventory.csv"
STRUCTURE_PATH = REPO_ROOT / "data/derived/manifests/mmrr21_extracted_structure.txt"


def repo_relative(path: Path) -> str:
    return path.resolve().relative_to(REPO_ROOT).as_posix()


def parse_subject_sources(path: Path) -> tuple[dict[str, str], dict[str, str]]:
    source_by_subject: dict[str, str] = {}
    repeat_evidence: dict[str, str] = {}
    in_repeat_table = False
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line == "Repeat scans:":
            in_repeat_table = True
            continue
        if not line or line.startswith("Mindboggle101,") or set(line) == {"-"}:
            continue
        if in_repeat_table:
            match = re.match(r"^(MMRR-21-\d+)\s+(.+)$", line)
            if match:
                repeat_evidence[match.group(1)] = match.group(2).strip()
            continue
        parts = [part.strip() for part in line.split(",")]
        if len(parts) == 5:
            subject, source = parts[0], parts[4]
            if subject in source_by_subject:
                raise ValueError(f"Duplicate subject-source row: {subject}")
            source_by_subject[subject] = source
    return source_by_subject, repeat_evidence


def parse_scan_information() -> dict[str, dict[str, str]]:
    member_name = "scans/MMRR-21/README_MMRR-21.txt"
    with tarfile.open(SCAN_INFO_ARCHIVE, "r:gz") as archive:
        member = archive.getmember(member_name)
        stream = archive.extractfile(member)
        if stream is None:
            raise ValueError(f"Could not read {member_name}")
        text = stream.read().decode("utf-8")
    rows: dict[str, dict[str, str]] = {}
    for match in re.finditer(r"^(\d+)\s+(\d+)\s+(\d+)\s+\d+\s+[mf]\s+\S+\s*$", text, re.MULTILINE):
        cohort_number, visit_id, scan_subject_id = match.groups()
        subject = f"MMRR-21-{cohort_number}"
        rows[subject] = {
            "scan_information_visit_id": visit_id,
            "scan_information_subject_id": scan_subject_id,
        }
    if len(rows) != 21:
        raise ValueError(f"Expected 21 scan-information rows, found {len(rows)}")
    return rows


def verify_extraction() -> tuple[int, int]:
    with tarfile.open(ARCHIVE_PATH, "r:gz") as archive:
        members = {member.name.rstrip("/").replace("\\", "/") for member in archive.getmembers()}
    disk_items = {
        path.relative_to(EXTRACT_TARGET).as_posix().rstrip("/")
        for path in EXTRACT_TARGET.rglob("*")
    }
    if members != disk_items:
        missing = sorted(members - disk_items)
        unexpected = sorted(disk_items - members)
        raise ValueError(
            f"Extracted tree mismatch: missing={len(missing)}, unexpected={len(unexpected)}"
        )
    return len(members), sum(path.is_file() for path in EXTRACT_TARGET.rglob("*"))


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    archive_member_count, extracted_file_count = verify_extraction()
    subject_list = {
        line.strip()
        for line in SUBJECT_LIST_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    }
    source_by_subject, repeat_evidence = parse_subject_sources(SUBJECT_SOURCES_PATH)
    scan_information = parse_scan_information()
    subject_directories = sorted(path for path in VOLUME_ROOT.iterdir() if path.is_dir())
    if len(subject_directories) != 21:
        raise ValueError(f"Expected 21 MMRR-21 directories, found {len(subject_directories)}")

    spaces = (
        {
            "space": "native",
            "mri": "t1weighted_brain.nii.gz",
            "label": "labels.DKT31.manual.nii.gz",
            "aux_mri": "t1weighted.nii.gz",
            "aux_label": "labels.DKT31.manual+aseg.nii.gz",
            "affine": "",
        },
        {
            "space": "MNI152",
            "mri": "t1weighted_brain.MNI152.nii.gz",
            "label": "labels.DKT31.manual.MNI152.nii.gz",
            "aux_mri": "t1weighted.MNI152.nii.gz",
            "aux_label": "labels.DKT31.manual+aseg.MNI152.nii.gz",
            "affine": "t1weighted_brain.MNI152.affine.txt",
        },
    )
    expected_nifti_names = {
        item[key]
        for item in spaces
        for key in ("mri", "label", "aux_mri", "aux_label")
    }
    rows: list[dict[str, str]] = []
    missing_or_ambiguous: list[str] = []
    for directory in subject_directories:
        subject = directory.name
        if subject not in subject_list:
            raise ValueError(f"Subject is absent from supplied subject list: {subject}")
        if subject not in source_by_subject:
            raise ValueError(f"Subject is absent from supplied subject-source table: {subject}")
        if subject not in scan_information:
            raise ValueError(f"Subject is absent from supplied scan information: {subject}")
        unexpected_nifti = sorted(
            path.name
            for path in directory.iterdir()
            if path.is_file() and (path.name.endswith(".nii") or path.name.endswith(".nii.gz"))
            and path.name not in expected_nifti_names
        )
        if unexpected_nifti:
            raise ValueError(f"Unexpected NIfTI for {subject}: {';'.join(unexpected_nifti)}")
        for space in spaces:
            paths = {key: directory / space[key] for key in ("mri", "label", "aux_mri", "aux_label")}
            if space["affine"]:
                paths["affine"] = directory / space["affine"]
            missing = [key for key, path in paths.items() if not path.is_file()]
            status = "matched_pending_nifti_qc" if not missing else "failed"
            reason = "" if not missing else "Missing required/expected file roles: " + ";".join(missing)
            if missing:
                missing_or_ambiguous.append(f"{subject}:{space['space']}:{reason}")
            evidence = repeat_evidence.get(subject, "")
            lineage_status = (
                "partial_explicit_repeat_mapping_recorded"
                if evidence
                else "partial_no_repeat_mapping_recorded"
            )
            rows.append(
                {
                    "scan_id": f"MMRR-21:{subject}:{space['space']}",
                    "participant_id": subject,
                    "source_subject_id": source_by_subject[subject],
                    "cohort": "MMRR-21",
                    "mri_path": repo_relative(paths["mri"]) if paths["mri"].is_file() else "",
                    "label_path": repo_relative(paths["label"]) if paths["label"].is_file() else "",
                    "space": space["space"],
                    "pairing_status": status,
                    "exclusion_reason": reason,
                    "subject_list_match": "verified",
                    "subject_source_match": "verified",
                    "scan_information_match": "verified",
                    **scan_information[subject],
                    "supplied_repeat_mapping": evidence,
                    "lineage_evidence_status": lineage_status,
                    "auxiliary_t1_path": repo_relative(paths["aux_mri"]) if paths["aux_mri"].is_file() else "",
                    "auxiliary_manual_aseg_path": repo_relative(paths["aux_label"]) if paths["aux_label"].is_file() else "",
                    "ancillary_affine_path": (
                        repo_relative(paths["affine"])
                        if "affine" in paths and paths["affine"].is_file()
                        else ""
                    ),
                    "notes": (
                        "Canonical skull-stripped T1/manual DKT31 pair selected by exact subject directory "
                        "and filename-declared space; full-head T1 and manual+aseg are auxiliary. "
                        "Lineage fields reproduce supplied metadata and do not resolve canonical scan/rescan identity."
                    ),
                }
            )
    write_csv(MANIFEST_PATH, rows)

    structure_lines = [
        "# Exact extracted directory structure for MMRR-21_volumes.tar.gz",
        "# Paths are repository-relative; directory paths end with /.",
        "# Recorded: 2026-08-26",
        "type\tpath\tsize_bytes",
    ]
    for path in sorted(EXTRACT_TARGET.rglob("*"), key=lambda item: item.as_posix()):
        relative = repo_relative(path) + ("/" if path.is_dir() else "")
        size = "" if path.is_dir() else str(path.stat().st_size)
        structure_lines.append(f"{'directory' if path.is_dir() else 'file'}\t{relative}\t{size}")
    STRUCTURE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STRUCTURE_PATH.write_text("\n".join(structure_lines) + "\n", encoding="utf-8")

    print(f"archive_members={archive_member_count} extracted_files={extracted_file_count}")
    print(f"subjects={len(subject_directories)} manifest_rows={len(rows)}")
    print(
        "native_candidates="
        f"{sum(row['space'] == 'native' and row['pairing_status'] == 'matched_pending_nifti_qc' for row in rows)}"
    )
    print(
        "mni152_candidates="
        f"{sum(row['space'] == 'MNI152' and row['pairing_status'] == 'matched_pending_nifti_qc' for row in rows)}"
    )
    print(f"missing_or_ambiguous={len(missing_or_ambiguous)}")
    print(f"explicit_repeat_mapping_subjects={len(repeat_evidence)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

