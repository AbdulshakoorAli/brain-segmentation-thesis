"""Safely extract and inventory a standard Mindboggle volume cohort."""

from __future__ import annotations

import argparse
import csv
import hashlib
import re
import tarfile
from collections import Counter
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw/mindboggle101"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def safe_members(archive: tarfile.TarFile) -> list[tarfile.TarInfo]:
    members = archive.getmembers()
    normalized = [member.name.replace("\\", "/").rstrip("/") for member in members]
    duplicates = [name for name, count in Counter(normalized).items() if count > 1]
    unsafe = []
    for member, name in zip(members, normalized):
        path = PurePosixPath(name)
        if path.is_absolute() or ".." in path.parts or (path.parts and ":" in path.parts[0]):
            unsafe.append(member.name)
        if not (member.isfile() or member.isdir()):
            unsafe.append(member.name)
    if duplicates or unsafe:
        raise ValueError(f"Unsafe archive: duplicates={duplicates}, unsafe={unsafe}")
    return members


def read_sources(cohort: str) -> dict[str, str]:
    path = RAW / "metadata/subject_sources_Mindboggle101.txt"
    rows: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        parts = [part.strip() for part in line.split(",")]
        if len(parts) == 5 and parts[0].startswith(cohort + "-"):
            rows[parts[0]] = parts[4]
    return rows


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cohort", required=True)
    parser.add_argument("--expected-subjects", required=True, type=int)
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument("--output-prefix")
    args = parser.parse_args()

    slug = args.output_prefix or re.sub(r"[^a-z0-9]+", "_", args.cohort.lower()).strip("_")
    archive_path = RAW / f"archives/volumes/{args.cohort}_volumes.tar.gz"
    target = RAW / f"extracted/{args.cohort}"
    digest = sha256(archive_path)
    if digest.lower() != args.expected_sha256.lower():
        raise ValueError(f"Archive checksum mismatch: {digest}")

    with tarfile.open(archive_path, "r:gz") as archive:
        members = safe_members(archive)
        if not target.exists():
            target.mkdir(parents=True)
            archive.extractall(target, filter="fully_trusted")

    with tarfile.open(archive_path, "r:gz") as archive:
        members = safe_members(archive)
    archive_names = {m.name.replace("\\", "/").rstrip("/") for m in members}
    disk_names = {p.relative_to(target).as_posix().rstrip("/") for p in target.rglob("*")}
    if archive_names != disk_names:
        raise ValueError(
            f"Extraction mismatch: missing={sorted(archive_names-disk_names)}, "
            f"unexpected={sorted(disk_names-archive_names)}"
        )

    volume_root = target / f"{args.cohort}_volumes"
    directories = sorted(
        (path for path in volume_root.iterdir() if path.is_dir()),
        key=lambda p: int(p.name.rsplit("-", 1)[1]),
    )
    if len(directories) != args.expected_subjects:
        raise ValueError(f"Expected {args.expected_subjects} subjects, found {len(directories)}")
    subject_list = {
        line.strip() for line in (RAW / "metadata/subject_list_Mindboggle101.txt")
        .read_text(encoding="utf-8").splitlines() if line.strip()
    }
    sources = read_sources(args.cohort)
    roles = {
        "t1weighted.nii.gz", "t1weighted_brain.nii.gz",
        "labels.DKT31.manual.nii.gz", "labels.DKT31.manual+aseg.nii.gz",
        "t1weighted.MNI152.nii.gz", "t1weighted_brain.MNI152.nii.gz",
        "labels.DKT31.manual.MNI152.nii.gz", "labels.DKT31.manual+aseg.MNI152.nii.gz",
    }
    spaces = [
        ("native", "t1weighted_brain.nii.gz", "labels.DKT31.manual.nii.gz",
         "t1weighted.nii.gz", "labels.DKT31.manual+aseg.nii.gz", ""),
        ("MNI152", "t1weighted_brain.MNI152.nii.gz", "labels.DKT31.manual.MNI152.nii.gz",
         "t1weighted.MNI152.nii.gz", "labels.DKT31.manual+aseg.MNI152.nii.gz",
         "t1weighted_brain.MNI152.affine.txt"),
    ]
    rows: list[dict[str, str]] = []
    missing: list[str] = []
    unexpected_nifti: list[str] = []
    for directory in directories:
        subject = directory.name
        if subject not in subject_list or subject not in sources:
            raise ValueError(f"Subject absent from supplied metadata: {subject}")
        unexpected_nifti.extend(
            f"{subject}/{p.name}" for p in directory.iterdir()
            if p.is_file() and (p.name.endswith(".nii") or p.name.endswith(".nii.gz"))
            and p.name not in roles
        )
        for space, mri, label, aux_t1, aux_label, affine in spaces:
            required = [directory / mri, directory / label, directory / aux_t1, directory / aux_label]
            if affine:
                required.append(directory / affine)
            absent = [p.name for p in required if not p.is_file()]
            if absent:
                missing.append(f"{subject}:{space}:{';'.join(absent)}")
            rel = lambda p: p.resolve().relative_to(ROOT).as_posix() if p.is_file() else ""
            rows.append({
                "scan_id": f"{args.cohort}:{subject}:{space}",
                "participant_id": subject,
                "source_subject_id": sources[subject],
                "cohort": args.cohort,
                "mri_path": rel(directory / mri),
                "label_path": rel(directory / label),
                "space": space,
                "pairing_status": "matched_pending_nifti_qc" if not absent else "failed",
                "exclusion_reason": "" if not absent else "Missing files: " + ";".join(absent),
                "subject_list_match": "verified",
                "subject_source_match": "verified",
                "participant_group_id": "",
                "acquisition_session_identifier": "",
                "lineage_resolution_status": "pending_metadata_review",
                "auxiliary_t1_path": rel(directory / aux_t1),
                "auxiliary_manual_aseg_path": rel(directory / aux_label),
                "ancillary_affine_path": rel(directory / affine) if affine else "",
                "unexpected_nifti_files": "",
                "notes": "Canonical skull-stripped T1/manual DKT31 pair selected within subject and declared space; full-head T1 and manual+aseg are auxiliary.",
            })
    if unexpected_nifti:
        raise ValueError(f"Unexpected NIfTI files: {unexpected_nifti}")
    manifest = ROOT / f"data/derived/manifests/{slug}_scan_inventory.csv"
    write_csv(manifest, rows)
    print(f"sha256={digest}")
    print(f"members={len(members)} files={sum(m.isfile() for m in members)} directories={sum(m.isdir() for m in members)}")
    print(f"subjects={len(directories)} nifti={sum(1 for p in target.rglob('*') if p.is_file() and (p.name.endswith('.nii') or p.name.endswith('.nii.gz')))}")
    print(f"native_candidates={sum(r['space']=='native' and r['pairing_status']=='matched_pending_nifti_qc' for r in rows)} mni152_candidates={sum(r['space']=='MNI152' and r['pairing_status']=='matched_pending_nifti_qc' for r in rows)}")
    print(f"missing_or_ambiguous={len(missing)} unexpected_nifti={len(unexpected_nifti)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
