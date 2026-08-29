"""Create evidence-traceable MMRR-21 lineage and label-issue records."""

from __future__ import annotations

import csv
import io
import re
import tarfile
from collections import defaultdict
from pathlib import Path

from pypdf import PdfReader


REPO_ROOT = Path(__file__).resolve().parents[1]
RAW_ROOT = REPO_ROOT / "data/raw/mindboggle101"
SUBJECT_LIST = RAW_ROOT / "metadata/subject_list_Mindboggle101.txt"
SUBJECT_SOURCES = RAW_ROOT / "metadata/subject_sources_Mindboggle101.txt"
LABEL_ISSUES = RAW_ROOT / "metadata/label-issues_201903.txt"
SCAN_INFO_ARCHIVE = RAW_ROOT / "archives/scan-information/subject_scans_info_Mindboggle101.tar.gz"
MANIFEST = REPO_ROOT / "data/derived/manifests/mmrr21_scan_inventory.csv"
QC = REPO_ROOT / "data/derived/qc/mmrr21_pair_qc.csv"
LINEAGE_OUTPUT = REPO_ROOT / "data/derived/metadata/mmrr21_lineage.csv"
ISSUE_OUTPUT = REPO_ROOT / "data/derived/metadata/mmrr21_label_issue_review.csv"

MMRR_PAPER_URL = "https://pmc.ncbi.nlm.nih.gov/articles/PMC3020263/"
MINDBOGGLE_PAPER_URL = (
    "https://www.frontiersin.org/journals/neuroscience/articles/"
    "10.3389/fnins.2012.00171/full"
)

LABEL_NAMES = {
    1032: "left frontal pole",
    1033: "left temporal pole",
    2032: "right frontal pole",
    2033: "right temporal pole",
}


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        return list(reader.fieldnames or []), list(reader)


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def archive_text(archive: tarfile.TarFile, member_name: str) -> str:
    stream = archive.extractfile(member_name)
    if stream is None:
        raise ValueError(f"Could not read archive member: {member_name}")
    return stream.read().decode("utf-8")


def archive_pdf_text(archive: tarfile.TarFile, member_name: str) -> str:
    stream = archive.extractfile(member_name)
    if stream is None:
        raise ValueError(f"Could not read archive member: {member_name}")
    reader = PdfReader(io.BytesIO(stream.read()))
    if len(reader.pages) != 1:
        raise ValueError(f"Expected one-page metadata PDF: {member_name}")
    return reader.pages[0].extract_text()


def parse_selected_scan_info(text: str) -> dict[str, dict[str, str]]:
    selected: dict[str, dict[str, str]] = {}
    for match in re.finditer(r"^(\d+)\s+(\d+)\s+(\d+)\s+\d+\s+[mf]\s+\S+\s*$", text, re.MULTILINE):
        cohort_number, visit_id, subject_id = match.groups()
        selected[f"MMRR-21-{cohort_number}"] = {
            "visit_id": visit_id.zfill(2),
            "subject_id": subject_id,
        }
    if len(selected) != 21:
        raise ValueError(f"Expected 21 selected scan-info rows, found {len(selected)}")
    return selected


def parse_all_sessions(text: str) -> dict[str, str]:
    visits: dict[str, str] = {}
    for line in text.splitlines():
        match = re.match(r"^(\d+)\s+(\d+)\s+", line.strip())
        if match:
            visit_id, subject_id = match.groups()
            visits[visit_id.zfill(2)] = subject_id
    if len(visits) != 42:
        raise ValueError(f"Expected 42 MMRR session rows, found {len(visits)}")
    grouped: dict[str, list[str]] = defaultdict(list)
    for visit_id, subject_id in visits.items():
        grouped[subject_id].append(visit_id)
    if len(grouped) != 21 or any(len(group) != 2 for group in grouped.values()):
        raise ValueError("MMRR demographics do not form 21 two-session participant groups")
    return visits


def parse_sources() -> tuple[dict[str, str], dict[str, str]]:
    source_by_subject: dict[str, str] = {}
    repeat_by_subject: dict[str, str] = {}
    in_repeats = False
    for line in SUBJECT_SOURCES.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped == "Repeat scans:":
            in_repeats = True
            continue
        if in_repeats:
            match = re.match(r"^(MMRR-21-\d+)\s+(.+)$", stripped)
            if match:
                repeat_by_subject[match.group(1)] = match.group(2)
            continue
        parts = [part.strip() for part in stripped.split(",")]
        if len(parts) == 5 and parts[0].startswith("MMRR-21-"):
            source_by_subject[parts[0]] = parts[4]
    if len(source_by_subject) != 21 or len(repeat_by_subject) != 10:
        raise ValueError("Unexpected MMRR subject-source or repeat-table counts")
    return source_by_subject, repeat_by_subject


def parse_issue_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for line_number, line in enumerate(LABEL_ISSUES.read_text(encoding="utf-8").splitlines(), start=1):
        match = re.match(r"^(MMRR-21-\d+)\.nii\.gz\s+\[([^]]+)\]$", line.strip())
        if not match:
            continue
        subject, raw_ids = match.groups()
        for raw_id in raw_ids.split():
            label_id = int(raw_id)
            if label_id not in LABEL_NAMES:
                raise ValueError(f"Undocumented MMRR issue label ID: {label_id}")
            rows.append(
                {
                    "affected_subject": subject,
                    "affected_label_id": str(label_id),
                    "anatomical_label_name": LABEL_NAMES[label_id],
                    "affected_file_product": f"{subject}.nii.gz (product unspecified by notice)",
                    "canonical_manual_dkt_affected": "no_observed_current_effect_native_or_mni152",
                    "recommended_action": "annotation_only",
                    "resolution_status": "historical_issue_corrected_current_canonical_clear_product_scope_unresolved",
                    "metadata_mentioned_not_observed": "yes",
                    "supporting_evidence": (
                        f"data/raw/mindboggle101/metadata/label-issues_201903.txt:{line_number}; "
                        "data/raw/mindboggle101/metadata/label_definitions.txt:27,140-200; "
                        "data/raw/mindboggle101/source_code/code_repostprocess_Mindboggle101.py:148-154,193-203; "
                        f"data/derived/qc/mmrr21_pair_qc.csv rows for {subject} native and MNI152"
                    ),
                    "notes": (
                        "The local notice states errors were corrected in March 2019 but does not identify a "
                        "specific distributed product. Repostprocessing retains DKT31 region numbers "
                        "2,3,5-31,34,35 and regenerates native/MNI152 manual volumes; accepted QC reports "
                        "zero occurrences of this metadata-mentioned ID in both canonical products."
                    ),
                }
            )
    if len(rows) != 6:
        raise ValueError(f"Expected 6 MMRR label-issue ID records, found {len(rows)}")
    return rows


def main() -> int:
    manifest_fields, manifest_rows = read_csv(MANIFEST)
    _, qc_rows = read_csv(QC)
    if len(manifest_rows) != 42 or len(qc_rows) != 42:
        raise ValueError("Expected 42 MMRR manifest and QC rows")
    if any(row["validation_status"] != "verified" for row in manifest_rows):
        raise ValueError("MMRR manifest contains a non-verified technical QC status")

    subject_list = {
        line.strip()
        for line in SUBJECT_LIST.read_text(encoding="utf-8").splitlines()
        if line.strip()
    }
    source_by_subject, repeat_by_subject = parse_sources()
    with tarfile.open(SCAN_INFO_ARCHIVE, "r:gz") as archive:
        selected = parse_selected_scan_info(
            archive_text(archive, "scans/MMRR-21/README_MMRR-21.txt")
        )
        all_sessions = parse_all_sessions(
            archive_pdf_text(archive, "scans/MMRR-21/MMRR_demographics.pdf")
        )

    visits_by_subject_id: dict[str, list[str]] = defaultdict(list)
    for visit_id, subject_id in all_sessions.items():
        visits_by_subject_id[subject_id].append(visit_id)
    for visits in visits_by_subject_id.values():
        visits.sort(key=int)

    issue_rows = parse_issue_rows()
    issue_ids_by_subject: dict[str, list[str]] = defaultdict(list)
    for issue in issue_rows:
        issue_ids_by_subject[issue["affected_subject"]].append(issue["affected_label_id"])

    qc_by_scan = {row["scan_id"]: row for row in qc_rows}
    lineage_rows: list[dict[str, str]] = []
    updated_manifest: list[dict[str, str]] = []
    for row in manifest_rows:
        scan_id = row["scan_id"]
        subject = row["participant_id"]
        if subject not in subject_list or subject not in selected or subject not in source_by_subject:
            raise ValueError(f"Missing local subject evidence for {subject}")
        visit_id = selected[subject]["visit_id"]
        subject_id = selected[subject]["subject_id"]
        source_id = source_by_subject[subject]
        if source_id != f"KKI2009-{visit_id}":
            raise ValueError(f"Source/Visit mismatch for {subject}: {source_id}, {visit_id}")
        if all_sessions.get(visit_id) != subject_id:
            raise ValueError(f"Selected/demographics SubjectID mismatch for {subject}")
        counterpart_visit = next(
            item for item in visits_by_subject_id[subject_id] if item != visit_id
        )
        counterpart_id = f"KKI2009-{counterpart_visit}"
        participant_group_id = f"MMRR-SubjectID-{subject_id}"
        subject_number = int(subject.rsplit("-", 1)[1])
        evidence_source = (
            "local subject list; local subject-source table; local scan-information README; "
            "local MMRR demographics PDF; original MMRR paper; primary Mindboggle-101 paper"
        )
        evidence_location = (
            f"data/raw/mindboggle101/metadata/subject_list_Mindboggle101.txt:{14 + subject_number}; "
            f"data/raw/mindboggle101/metadata/subject_sources_Mindboggle101.txt:{31 + subject_number}; "
            "data/raw/mindboggle101/archives/scan-information/"
            "subject_scans_info_Mindboggle101.tar.gz::scans/MMRR-21/README_MMRR-21.txt, "
            f"Subjects row {subject_number}; same archive::scans/MMRR-21/MMRR_demographics.pdf, "
            f"page 1 Visit ID rows {int(visit_id)} and {int(counterpart_visit)}; "
            f"{MMRR_PAPER_URL} Methods lines 242-245; "
            f"{MINDBOGGLE_PAPER_URL} Data lines 364,379,394"
        )
        resolution_status = "participant_and_repeat_group_resolved_scan_rescan_role_unresolved"
        lineage = {
            "scan_id": scan_id,
            "source_subject_id": source_id,
            "participant_group_id": participant_group_id,
            "acquisition_session_identifier": source_id,
            "scan_or_rescan_role": "unresolved_randomized_session_role",
            "evidence_source": evidence_source,
            "exact_evidence_location": evidence_location,
            "resolution_status": resolution_status,
            "notes": (
                f"The {row['space']} row is a derived representation of included session {source_id}; "
                f"the other space row is the same acquisition, not a repeat. {counterpart_id} is the "
                "confirmed other session for this participant and is not an MMRR-21 canonical row. "
                "Session codes were randomized, so temporal scan/rescan role is unsupported."
            ),
            "space": row["space"],
            "counterpart_acquisition_session_identifier": counterpart_id,
            "lineage_classification": "distinct_included_participant_with_confirmed_external_repeat",
        }
        lineage_rows.append(lineage)

        mentioned_ids = sorted(issue_ids_by_subject.get(subject, []), key=int)
        updated = dict(row)
        updated.update(
            {
                "participant_group_id": participant_group_id,
                "acquisition_session_identifier": source_id,
                "counterpart_acquisition_session_identifier": counterpart_id,
                "scan_rescan_role": "unresolved_randomized_session_role",
                "lineage_resolution_status": resolution_status,
                "lineage_evidence_source": evidence_source,
                "lineage_evidence_location": evidence_location,
                "label_issue_review_status": (
                    "historical_correction_current_canonical_clear_product_scope_unresolved"
                    if mentioned_ids
                    else "no_mmrr21_label_issue_entry"
                ),
                "label_issue_metadata_ids": ";".join(mentioned_ids),
                "label_issue_action": "annotation_only" if mentioned_ids else "no_action",
                "label_issue_evidence": (
                    "data/raw/mindboggle101/metadata/label-issues_201903.txt; "
                    "data/raw/mindboggle101/source_code/code_repostprocess_Mindboggle101.py:193-203; "
                    "data/derived/qc/mmrr21_pair_qc.csv"
                    if mentioned_ids
                    else "data/raw/mindboggle101/metadata/label-issues_201903.txt"
                ),
            }
        )
        if qc_by_scan[scan_id].get("unknown_label_ids"):
            raise ValueError(f"Accepted QC unexpectedly contains unknown IDs for {scan_id}")
        updated_manifest.append(updated)

    if len({row["participant_group_id"] for row in lineage_rows}) != 21:
        raise ValueError("Lineage records do not contain exactly 21 participant groups")
    if len({
        tuple(sorted((row["acquisition_session_identifier"], row["counterpart_acquisition_session_identifier"])))
        for row in lineage_rows
    }) != 21:
        raise ValueError("Lineage records do not contain exactly 21 repeat-acquisition groups")

    lineage_fields = [
        "scan_id", "source_subject_id", "participant_group_id",
        "acquisition_session_identifier", "scan_or_rescan_role", "evidence_source",
        "exact_evidence_location", "resolution_status", "notes", "space",
        "counterpart_acquisition_session_identifier", "lineage_classification",
    ]
    issue_fields = [
        "affected_subject", "affected_label_id", "anatomical_label_name",
        "affected_file_product", "canonical_manual_dkt_affected", "recommended_action",
        "resolution_status", "metadata_mentioned_not_observed", "supporting_evidence", "notes",
    ]
    new_manifest_fields = [
        "participant_group_id", "acquisition_session_identifier",
        "counterpart_acquisition_session_identifier", "scan_rescan_role",
        "lineage_resolution_status", "lineage_evidence_source", "lineage_evidence_location",
        "label_issue_review_status", "label_issue_metadata_ids", "label_issue_action",
        "label_issue_evidence",
    ]
    write_csv(LINEAGE_OUTPUT, lineage_fields, lineage_rows)
    write_csv(ISSUE_OUTPUT, issue_fields, issue_rows)
    write_csv(
        MANIFEST,
        manifest_fields + [field for field in new_manifest_fields if field not in manifest_fields],
        updated_manifest,
    )
    print("lineage_rows=42 participant_groups=21 repeat_acquisition_groups=21")
    print("scan_rescan_role_resolved=0 scan_rescan_role_unresolved=42")
    print("label_issue_rows=6 exclusions=0 annotation_only=6")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
