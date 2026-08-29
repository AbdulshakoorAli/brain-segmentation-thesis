"""Generate evidence-traceable NKI-RS-22 lineage and label-issue metadata."""

from __future__ import annotations

import csv
import io
import re
import tarfile
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw/mindboggle101"
SCAN_INFO = RAW / "archives/scan-information/subject_scans_info_Mindboggle101.tar.gz"
MANIFEST = ROOT / "data/derived/manifests/nki_rs22_scan_inventory.csv"
QC = ROOT / "data/derived/qc/nki_rs22_pair_qc.csv"
LINEAGE = ROOT / "data/derived/metadata/nki_rs22_lineage.csv"
ISSUES = ROOT / "data/derived/metadata/nki_rs22_label_issue_review.csv"

NAMES = {
    7: "left cerebellum white matter", 16: "Brain stem", 24: "CSF",
    46: "right cerebellum white matter", 85: "optic chiasm",
    1033: "left temporal pole", 2033: "right temporal pole",
}


def read(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream); return list(reader.fieldnames or []), list(reader)


def write(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader(); writer.writerows(rows)


def sources() -> dict[str, str]:
    rows = {}
    for line in (RAW/"metadata/subject_sources_Mindboggle101.txt").read_text(encoding="utf-8").splitlines():
        parts = [x.strip() for x in line.split(",")]
        if len(parts) == 5 and parts[0].startswith("NKI-RS-22-"):
            rows[parts[0]] = parts[4]
    if len(rows) != 22 or len(set(rows.values())) != 22:
        raise ValueError("Expected 22 unique NKI source subjects")
    return rows


def scan_metadata() -> tuple[dict[str, str], dict[str, dict[str, str]]]:
    with tarfile.open(SCAN_INFO, "r:gz") as archive:
        selected_stream = io.TextIOWrapper(
            archive.extractfile("scans/NKI-RS-22/NKI-RS-22.phenotypic_best22of40-mri-fmri-dti_20-40yrs.csv"),
            encoding="utf-8-sig",
        )
        selected_rows = list(csv.reader(selected_stream, delimiter="\t"))
        qc_stream = io.TextIOWrapper(
            archive.extractfile("scans/NKI-RS-22/NKI.1-39.NumbersQC.csv"), encoding="utf-8-sig"
        )
        qc_rows = list(csv.DictReader(qc_stream))
    selected = {row[1]: row[50] for row in selected_rows}
    qc = {
        row["Subject"]: {
            "session": row["Session_M"], "scan_id": row["Scan ID M"],
            "scan_type": row["Scan Type M"],
            "quality_call": row["Quality Call (pass/questionable/fail) M"].strip(),
            "comments": row["Comments M"].strip(),
        }
        for row in qc_rows if row["Subject"] in selected
    }
    if len(selected) != 22 or len(qc) != 22:
        raise ValueError("Expected 22 selected and QC metadata rows")
    return selected, qc


def issue_rows() -> list[dict[str, str]]:
    rows = []
    text = (RAW/"metadata/label-issues_201903.txt").read_text(encoding="utf-8")
    for line_number, line in enumerate(text.splitlines(), 1):
        match = re.match(r"^(NKI-RS-22-\d+)\.nii\.gz\s+\[([^]]+)\]$", line.strip())
        if not match: continue
        subject, ids = match.groups()
        for token in ids.split():
            label_id = int(token)
            cortical_pole = label_id in {1033, 2033}
            rows.append({
                "affected_subject": subject,
                "affected_label_id": str(label_id),
                "anatomical_label_name": NAMES.get(label_id, ""),
                "affected_file_product": f"{subject}.nii.gz (product unspecified by notice)",
                "canonical_manual_dkt_affected": "no_observed_current_effect_native_or_mni152",
                "required_action": "annotation_only" if cortical_pole else "not_applicable",
                "resolution_status": (
                    "historical_corrected_pole_id_absent_product_scope_unresolved" if cortical_pole
                    else "outside_canonical_dkt31_vocabulary_product_scope_unresolved"
                ),
                "metadata_mentioned_not_observed": "yes",
                "supporting_evidence": (
                    f"data/raw/mindboggle101/metadata/label-issues_201903.txt:{line_number}; "
                    "data/raw/mindboggle101/metadata/label_definitions.txt:27,140-200,220-260; "
                    "data/raw/mindboggle101/source_code/code_repostprocess_Mindboggle101.py:148-154,195-203; "
                    f"data/derived/qc/nki_rs_22_pair_qc.csv rows for {subject}"
                ),
                "notes": (
                    "The notice states errors were corrected in March 2019 but does not identify the distributed product. "
                    "Current canonical DKT31 volumes contain none of this ID. IDs outside the accepted 62-label DKT31 "
                    "selection are not applicable to the canonical target; the notice remains auxiliary provenance."
                ),
            })
    if len(rows) != 18:
        raise ValueError(f"Expected 18 NKI issue-ID rows, found {len(rows)}")
    return rows


def main() -> int:
    fields, manifest = read(MANIFEST); _, qc_rows = read(QC)
    if len(manifest) != 44 or len(qc_rows) != 44 or any(r["validation_status"] != "verified" for r in qc_rows):
        raise ValueError("Expected 44 technically verified NKI rows")
    source_by_subject = sources(); selected, scan_qc = scan_metadata(); issues = issue_rows()
    issue_by_subject: dict[str, list[dict[str, str]]] = defaultdict(list)
    for issue in issues: issue_by_subject[issue["affected_subject"]].append(issue)
    lineage=[]; updated=[]
    for row in manifest:
        subject=row["participant_id"]; source=source_by_subject[subject]
        source_number=source.removeprefix("NKI_Rockland_")
        if source_number not in selected or source_number not in scan_qc:
            raise ValueError(f"Missing scan metadata for {subject}")
        selected_session=selected[source_number]; qc_session=scan_qc[source_number]["session"]
        matched=selected_session == qc_session
        session=selected_session if matched else ""
        status="participant_and_acquisition_resolved_no_repeat_evidence" if matched else "participant_resolved_acquisition_session_ambiguous"
        group=f"NKI-Rockland-{source_number}"
        n=int(subject.rsplit("-",1)[1])
        evidence_source="local subject list; local subject-source table; local selected-22 phenotype table; local NKI MRI QC table"
        evidence_location=(
            f"data/raw/mindboggle101/metadata/subject_list_Mindboggle101.txt:{37+n}; "
            f"data/raw/mindboggle101/metadata/subject_sources_Mindboggle101.txt:{54+n}; "
            "data/raw/mindboggle101/archives/scan-information/subject_scans_info_Mindboggle101.tar.gz::"
            f"scans/NKI-RS-22/NKI-RS-22.phenotypic_best22of40-mri-fmri-dti_20-40yrs.csv row {n}; "
            f"same archive::scans/NKI-RS-22/NKI.1-39.NumbersQC.csv Subject {source_number}"
        )
        note=(f"The {row['space']} row is the same included acquisition as the other coordinate-space row. "
              "No supplied repeat mapping links this source subject to another included NKI-RS-22 subject. ")
        if not matched:
            note += f"Selected-22 table reports {selected_session}, while MRI QC reports {qc_session}; acquisition/session is unresolved."
        else:
            note += f"Selected-22 and MRI QC tables agree on session {session}."
        lineage.append({
            "scan_id":row["scan_id"],"source_subject_id":source,"participant_group_id":group,
            "acquisition_session_identifier":session,"candidate_session_identifiers":selected_session if matched else f"{selected_session};{qc_session}",
            "scan_or_rescan_role":"unresolved_no_repeat_role_evidence","evidence_source":evidence_source,
            "exact_evidence_location":evidence_location,"resolution_status":status,"notes":note,
            "space":row["space"],"repeat_acquisition_evidence":"none_in_supplied_mindboggle_metadata",
            "mri_qc_scan_id":scan_qc[source_number]["scan_id"],"mri_qc_scan_type":scan_qc[source_number]["scan_type"],
            "mri_qc_quality_call":scan_qc[source_number]["quality_call"],
        })
        subject_issues=issue_by_subject.get(subject,[]); ids=sorted({x["affected_label_id"] for x in subject_issues},key=int)
        actions=sorted({x["required_action"] for x in subject_issues})
        item=dict(row); item.update({
            "participant_group_id":group,"acquisition_session_identifier":session,
            "candidate_session_identifiers":selected_session if matched else f"{selected_session};{qc_session}",
            "scan_rescan_role":"unresolved_no_repeat_role_evidence","lineage_resolution_status":status,
            "lineage_evidence_source":evidence_source,"lineage_evidence_location":evidence_location,
            "repeat_acquisition_evidence":"none_in_supplied_mindboggle_metadata",
            "label_issue_review_status":"reviewed_issue_entries" if ids else "no_nki_rs22_issue_entry",
            "label_issue_metadata_ids":";".join(ids),"label_issue_action":";".join(actions) if actions else "no_action",
            "label_issue_evidence":"data/raw/mindboggle101/metadata/label-issues_201903.txt" if ids else "same file; no subject entry",
        }); updated.append(item)
    if len({r["participant_group_id"] for r in lineage}) != 22:
        raise ValueError("Participant groups are not unique")
    if sum(not r["acquisition_session_identifier"] for r in lineage) != 2:
        raise ValueError("Expected two space records for one ambiguous acquisition")
    lineage_fields=list(lineage[0]); issue_fields=list(issues[0])
    additions=[f for f in updated[0] if f not in fields]
    write(LINEAGE,lineage_fields,lineage); write(ISSUES,issue_fields,issues); write(MANIFEST,fields+additions,updated)
    print("lineage_rows=44 participant_groups_confirmed=22 participant_groups_unresolved=0")
    print("acquisitions_resolved=21 acquisitions_ambiguous=1 repeat_groups_confirmed=0")
    print(f"label_issue_rows={len(issues)} annotation_only={sum(x['required_action']=='annotation_only' for x in issues)} not_applicable={sum(x['required_action']=='not_applicable' for x in issues)} exclusions=0 unresolved_actions=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
