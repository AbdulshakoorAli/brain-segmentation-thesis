"""Create OASIS-TRT-20 lineage, label-issue, and overlap records."""

from __future__ import annotations

import csv
import re
import tarfile
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw/mindboggle101"
SCAN_INFO = RAW / "archives/scan-information/subject_scans_info_Mindboggle101.tar.gz"
MANIFEST = ROOT / "data/derived/manifests/oasis_trt20_scan_inventory.csv"
QC = ROOT / "data/derived/qc/oasis_trt20_pair_qc.csv"
LINEAGE = ROOT / "data/derived/metadata/oasis_trt20_lineage.csv"
ISSUES = ROOT / "data/derived/metadata/oasis_trt20_label_issue_review.csv"
OVERLAP = ROOT / "data/derived/metadata/oasis_overlap_review.csv"
OASIS_PAGE = "https://sites.wustl.edu/oasisbrains/home/oasis-1/"
OASIS_PAPER = "https://pubmed.ncbi.nlm.nih.gov/17714011/"

POLE_NAMES = {
    1032: "left frontal pole", 1033: "left temporal pole",
    2032: "right frontal pole", 2033: "right temporal pole",
}


def read(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream); return list(reader.fieldnames or []), list(reader)


def write(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader(); writer.writerows(rows)


def source_rows() -> tuple[dict[str, str], dict[str, list[str]]]:
    selected={}; by_participant:dict[str,list[str]]=defaultdict(list)
    for line in (RAW/"metadata/subject_sources_Mindboggle101.txt").read_text(encoding="utf-8").splitlines():
        parts=[x.strip() for x in line.split(",")]
        if len(parts)!=5: continue
        subject, source=parts[0],parts[4]
        if subject.startswith("OASIS-TRT-20-"): selected[subject]=source
        if re.fullmatch(r"OAS1_\d+_MR\d+",source): by_participant[source.rsplit("_MR",1)[0]].append(subject)
    if len(selected)!=20 or len(set(selected.values()))!=20: raise ValueError("Expected 20 unique OASIS source sessions")
    return selected,by_participant


def readme_sessions() -> dict[str,dict[str,str]]:
    member="scans/OASIS-TRT-20/README_OASIS-TRT-20.txt"
    with tarfile.open(SCAN_INFO,"r:gz") as archive:
        stream=archive.extractfile(member)
        if stream is None: raise ValueError("Missing OASIS README")
        text=stream.read().decode("utf-8-sig")
    rows={}
    pattern=r"^\d+\s+(OAS1_(\d+)_MR([12]))\s+(OAS1_\d+)\s+[MF]\s+[RLA]\s+\d+\s+\S+\s+\S+\s+\S+(?:\s+(\d+))?\s+(TEST|RETEST)\s+"
    for match in re.finditer(pattern,text,re.MULTILINE):
        session,number,mr,participant,delay,role=match.groups()
        rows[session]={"participant":participant,"mr":mr,"role":role.lower(),"delay_days":delay or ""}
    if len(rows)!=40: raise ValueError(f"Expected 40 OASIS test/retest rows, found {len(rows)}")
    return rows


def issue_rows() -> list[dict[str,str]]:
    rows=[]; text=(RAW/"metadata/label-issues_201903.txt").read_text(encoding="utf-8")
    for line_number,line in enumerate(text.splitlines(),1):
        match=re.match(r"^(OASIS-TRT-20-\d+)\.nii\.gz\s+\[([^]]+)\]$",line.strip())
        if not match: continue
        subject,block=match.groups()
        for token in block.split():
            label_id=int(token)
            if label_id not in POLE_NAMES: raise ValueError(f"Unexpected OASIS issue ID {label_id}")
            rows.append({
                "affected_subject":subject,"affected_label_id":str(label_id),
                "anatomical_label_name":POLE_NAMES[label_id],
                "affected_file_product":f"{subject}.nii.gz (product unspecified by notice)",
                "canonical_manual_dkt_affected":"no_observed_current_effect_native_or_mni152",
                "required_action":"annotation_only",
                "resolution_status":"historical_corrected_pole_id_absent_product_scope_unresolved",
                "metadata_mentioned_not_observed":"yes",
                "supporting_evidence":(
                    f"data/raw/mindboggle101/metadata/label-issues_201903.txt:{line_number}; "
                    "data/raw/mindboggle101/metadata/label_definitions.txt:27,140-200; "
                    "data/raw/mindboggle101/source_code/code_repostprocess_Mindboggle101.py:148-154,195-203; "
                    f"data/derived/qc/oasis_trt20_pair_qc.csv rows for {subject}"
                ),
                "notes":"The notice says errors were corrected in March 2019 but does not specify the product. The eliminated pole ID is absent from both current canonical DKT31 volumes.",
            })
    if len(rows)!=9 or len({r["affected_subject"] for r in rows})!=8:
        raise ValueError("Expected 9 OASIS issue-ID rows across eight subjects")
    return rows


def main() -> int:
    fields,manifest=read(MANIFEST); _,qc=read(QC)
    if len(manifest)!=40 or len(qc)!=40 or any(r["validation_status"]!="verified" for r in qc):
        raise ValueError("Expected 40 verified OASIS records")
    sources,all_oasis=source_rows(); sessions=readme_sessions(); issues=issue_rows()
    accepted=[]
    for name in ["extra18_pair_qc.csv","mmrr21_pair_qc.csv","nki_rs22_pair_qc.csv","nki_trt20_pair_qc.csv"]:
        accepted.extend(read(ROOT/"data/derived/qc"/name)[1])
    hash_sets={k:{r[k] for r in accepted} for k in ["mri_file_sha256","label_file_sha256","mri_voxel_sha256","label_voxel_sha256"]}
    qc_by={r["scan_id"]:r for r in qc}; issue_by:dict[str,list[dict[str,str]]]=defaultdict(list)
    for issue in issues: issue_by[issue["affected_subject"]].append(issue)
    lineage=[]; overlap=[]; updated=[]
    for row in manifest:
        subject=row["participant_id"]; source=sources[subject]
        if source not in sessions: raise ValueError(f"Source session absent from README: {source}")
        evidence=sessions[source]; participant=evidence["participant"]
        counterpart=f"{participant}_MR{'2' if evidence['mr']=='1' else '1'}"
        if counterpart not in sessions: raise ValueError(f"Missing counterpart: {counterpart}")
        group=f"OASIS1-{participant}"; repeat_group=f"OASIS1-repeat-{participant}"
        number=int(subject.rsplit("-",1)[1])
        evidence_source="local subject list; local subject-source table; local OASIS reliability README; official OASIS-1 documentation; primary OASIS-1 paper"
        evidence_location=(
            f"data/raw/mindboggle101/metadata/subject_list_Mindboggle101.txt:{79+number}; "
            f"data/raw/mindboggle101/metadata/subject_sources_Mindboggle101.txt:{96+number}; "
            "data/raw/mindboggle101/archives/scan-information/subject_scans_info_Mindboggle101.tar.gz::"
            f"scans/OASIS-TRT-20/README_OASIS-TRT-20.txt rows {source} and {counterpart}; "
            f"{OASIS_PAGE}; {OASIS_PAPER}"
        )
        note=(f"The {row['space']} row is a coordinate-space representation of included session {source}, not a repeat. "
              f"The supplied README identifies {source} as {evidence['role'].upper()} and {counterpart} as its other session.")
        lineage.append({
            "scan_id":row["scan_id"],"source_subject_id":source,"source_participant_identifier":participant,
            "participant_group_id":group,"acquisition_session_identifier":source,
            "scan_or_rescan_role":evidence["role"],"repeat_acquisition_group":repeat_group,
            "counterpart_acquisition_session_identifier":counterpart,
            "evidence_source":evidence_source,"exact_evidence_location":evidence_location,
            "resolution_status":"participant_acquisition_role_and_repeat_group_resolved",
            "notes":note,"space":row["space"],
        })
        q=qc_by[row["scan_id"]]
        file_dup=q["mri_file_sha256"] in hash_sets["mri_file_sha256"] or q["label_file_sha256"] in hash_sets["label_file_sha256"]
        voxel_dup=q["mri_voxel_sha256"] in hash_sets["mri_voxel_sha256"] or q["label_voxel_sha256"] in hash_sets["label_voxel_sha256"]
        other_mb=sorted(x for x in all_oasis.get(participant,[]) if x!=subject)
        if row["space"]=="native": overlap.append({
            "oasis_trt_subject":subject,"source_participant_identifier":participant,
            "participant_group_id":group,"included_session_identifier":source,
            "included_scan_rescan_role":evidence["role"],"counterpart_session_identifier":counterpart,
            "other_mindboggle_overlap_subjects":";".join(other_mb),
            "oasis1_reliability_overlap":"confirmed",
            "other_external_oasis_release_overlap":"unresolved_not_documented",
            "exact_file_duplicate_with_accepted_cohorts":"yes" if file_dup else "no",
            "exact_voxel_duplicate_with_accepted_cohorts":"yes" if voxel_dup else "no",
            "relationship_status":"confirmed_oasis1_participant_and_external_repeat_no_other_mindboggle_match",
            "evidence_source":"subject_sources_Mindboggle101; OASIS reliability README; accepted QC hashes; official OASIS-1 documentation; primary OASIS-1 paper",
            "exact_evidence_location":evidence_location,
            "notes":"External overlap is with the OASIS-1 cross-sectional reliability release. No evidence was found linking this participant to another OASIS release.",
        })
        subject_issues=issue_by.get(subject,[]); ids=sorted({x["affected_label_id"] for x in subject_issues},key=int)
        item=dict(row); item.update({
            "source_participant_identifier":participant,"participant_group_id":group,
            "acquisition_session_identifier":source,"scan_rescan_role":evidence["role"],
            "repeat_acquisition_group":repeat_group,"counterpart_acquisition_session_identifier":counterpart,
            "lineage_resolution_status":"participant_acquisition_role_and_repeat_group_resolved",
            "lineage_evidence_source":evidence_source,"lineage_evidence_location":evidence_location,
            "label_issue_review_status":"reviewed_issue_entries" if ids else "no_oasis_trt20_issue_entry",
            "label_issue_metadata_ids":";".join(ids),"label_issue_action":"annotation_only" if ids else "no_action",
            "label_issue_evidence":"data/raw/mindboggle101/metadata/label-issues_201903.txt" if ids else "same file; no subject entry",
        }); updated.append(item)
    if len({r["participant_group_id"] for r in lineage})!=20 or len({r["repeat_acquisition_group"] for r in lineage})!=20:
        raise ValueError("Expected 20 participant and repeat groups")
    if sum(r["scan_or_rescan_role"]=="test" for r in lineage)!=36 or sum(r["scan_or_rescan_role"]=="retest" for r in lineage)!=4:
        raise ValueError("Expected 18 test and 2 retest acquisitions across two spaces")
    if len(overlap)!=20 or any(r["other_mindboggle_overlap_subjects"] for r in overlap):
        raise ValueError("Unexpected Mindboggle OASIS participant overlap")
    additions=[f for f in updated[0] if f not in fields]
    write(LINEAGE,list(lineage[0]),lineage); write(ISSUES,list(issues[0]),issues)
    write(OVERLAP,list(overlap[0]),overlap); write(MANIFEST,fields+additions,updated)
    print("lineage_rows=40 participant_groups_confirmed=20 participant_groups_unresolved=0 repeat_groups_confirmed=20")
    print("included_test_acquisitions=18 included_retest_acquisitions=2 other_mindboggle_participant_overlaps=0 oasis1_external_overlaps=20")
    print("label_issue_rows=9 issue_subjects=8 annotation_only=9 exclusions=0 not_applicable=0 unresolved_actions=0")
    return 0


if __name__ == "__main__": raise SystemExit(main())
