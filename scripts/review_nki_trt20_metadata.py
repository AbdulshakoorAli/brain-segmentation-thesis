"""Create NKI-TRT-20 lineage, label-issue, and cross-cohort overlap records."""

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
MANIFEST = ROOT / "data/derived/manifests/nki_trt20_scan_inventory.csv"
QC = ROOT / "data/derived/qc/nki_trt20_pair_qc.csv"
LINEAGE = ROOT / "data/derived/metadata/nki_trt20_lineage.csv"
ISSUES = ROOT / "data/derived/metadata/nki_trt20_label_issue_review.csv"
OVERLAP = ROOT / "data/derived/metadata/nki_cross_cohort_overlap_review.csv"
OFFICIAL_TRT = "https://fcon_1000.projects.nitrc.org/indi/pro/eNKI_RS_TRT/FrontPage.html"
PRIMARY_NKI = "https://doi.org/10.3389/fnins.2012.00152"


def read(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream); return list(reader.fieldnames or []), list(reader)


def write(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader(); writer.writerows(rows)


def source_rows() -> tuple[dict[str, str], dict[str, list[str]]]:
    trt: dict[str, str] = {}; all_by_nki_id: dict[str, list[str]] = defaultdict(list)
    for line in (RAW/"metadata/subject_sources_Mindboggle101.txt").read_text(encoding="utf-8").splitlines():
        parts = [item.strip() for item in line.split(",")]
        if len(parts) != 5: continue
        subject, source = parts[0], parts[4]
        if subject.startswith("NKI-TRT-20-"): trt[subject] = source
        normalized = source.removeprefix("NKI_Rockland_").lstrip("0")
        if normalized.isdigit(): all_by_nki_id[normalized].append(subject)
    if len(trt) != 20 or len(set(trt.values())) != 20:
        raise ValueError("Expected 20 unique NKI-TRT source IDs")
    return trt, all_by_nki_id


def scan_info() -> tuple[dict[int, str], dict[str, dict[str, str]]]:
    with tarfile.open(SCAN_INFO, "r:gz") as archive:
        phenotype = list(csv.reader(io.TextIOWrapper(
            archive.extractfile("scans/NKI-TRT-20/NKI-TRT-20.phenotypic.csv"),
            encoding="utf-8-sig"), delimiter="\t"))
        external = list(csv.DictReader(io.TextIOWrapper(
            archive.extractfile("scans/NKI-RS-22/NKI.1-39.NumbersQC.csv"),
            encoding="utf-8-sig")))
    selected = {int(row[0]): row[1] for row in phenotype[1:] if row and row[0].isdigit()}
    wider = {row["Subject"]: row for row in external}
    if len(selected) != 20: raise ValueError("Expected 20 NKI-TRT phenotype rows")
    return selected, wider


def label_names() -> dict[int, str]:
    text = (RAW/"metadata/label_definitions.txt").read_text(encoding="utf-8")
    return {int(number): name for number, name in re.findall(r'\[(\d+),\s*"([^"]+)"\]', text)}


def issue_rows() -> list[dict[str, str]]:
    text = (RAW/"metadata/label-issues_201903.txt").read_text(encoding="utf-8")
    names = label_names(); rows=[]
    for match in re.finditer(r"^(NKI-TRT-20-\d+)\.nii\.gz\s+\[([^]]+)\]", text, re.MULTILINE):
        subject, block = match.groups()
        line_number = text[:match.start()].count("\n") + 1
        for token in re.findall(r"\d+", block):
            label_id=int(token); pole=label_id in {1033,2033}
            rows.append({
                "affected_subject":subject,"affected_label_id":str(label_id),
                "anatomical_label_name":names.get(label_id,""),
                "affected_file_product":f"{subject}.nii.gz (product unspecified by notice)",
                "canonical_manual_dkt_affected":"no_observed_current_effect_native_or_mni152",
                "required_action":"annotation_only" if pole else "not_applicable_to_canonical_DKT31",
                "resolution_status":"historical_corrected_metadata_id_absent_product_scope_unresolved",
                "metadata_mentioned_not_observed":"yes",
                "supporting_evidence":(
                    f"data/raw/mindboggle101/metadata/label-issues_201903.txt:{line_number}; "
                    "data/raw/mindboggle101/metadata/label_definitions.txt; "
                    "data/raw/mindboggle101/source_code/code_repostprocess_Mindboggle101.py:148-154,195-203; "
                    f"data/derived/qc/nki_trt20_pair_qc.csv rows for {subject}"
                ),
                "notes":"The notice says errors were corrected in March 2019 but does not specify the product. The ID is absent from both current canonical DKT31 volumes; non-pole IDs are outside the accepted 62-label canonical selection.",
            })
    if not rows or len({r["affected_subject"] for r in rows}) != 8:
        raise ValueError("Expected label-issue entries for eight NKI-TRT subjects")
    return rows


def main() -> int:
    fields, manifest=read(MANIFEST); _, qc=read(QC)
    if len(manifest)!=40 or len(qc)!=40 or any(r["validation_status"]!="verified" for r in qc):
        raise ValueError("Expected 40 verified NKI-TRT records")
    trt_sources, all_sources=source_rows(); phenotype, wider=scan_info(); issues=issue_rows()
    _, rs_manifest=read(ROOT/"data/derived/manifests/nki_rs22_scan_inventory.csv")
    rs_by_source: dict[str,set[str]]=defaultdict(set)
    for row in rs_manifest:
        rs_by_source[row["source_subject_id"].removeprefix("NKI_Rockland_").lstrip("0")].add(row["participant_id"])
    accepted=[]
    for name in ["extra18_pair_qc.csv","mmrr21_pair_qc.csv","nki_rs22_pair_qc.csv"]:
        accepted.extend(read(ROOT/"data/derived/qc"/name)[1])
    hash_indexes={key:{r[key] for r in accepted} for key in ["mri_file_sha256","label_file_sha256","mri_voxel_sha256","label_voxel_sha256"]}
    qc_by_scan={r["scan_id"]:r for r in qc}; issue_by_subject:dict[str,list[dict[str,str]]]=defaultdict(list)
    for issue in issues: issue_by_subject[issue["affected_subject"]].append(issue)
    lineage=[]; overlap=[]; updated=[]
    for row in manifest:
        subject=row["participant_id"]; number=int(subject.rsplit("-",1)[1]); source=trt_sources[subject]
        normalized=source.lstrip("0")
        if int(phenotype[number]) != int(source): raise ValueError(f"Phenotype/source mismatch: {subject}")
        group=f"NKI-Rockland-{source}"; repeat_group=f"NKI-TRT-repeat-{source}"
        rs_subjects=sorted(rs_by_source.get(normalized,set()),key=lambda x:int(x.rsplit('-',1)[1]))
        other_mb=sorted(x for x in all_sources.get(normalized,[]) if x!=subject and x not in rs_subjects)
        ext=wider.get(normalized); ext_session=ext["Session_M"] if ext else ""
        evidence_source="local subject list; local subject-source table; local NKI-TRT phenotype table; local NKI-TRT README; official NKI test-retest documentation; primary NKI paper"
        evidence_location=(
            f"data/raw/mindboggle101/metadata/subject_list_Mindboggle101.txt:{59+number}; "
            f"data/raw/mindboggle101/metadata/subject_sources_Mindboggle101.txt:{76+number}; "
            "data/raw/mindboggle101/archives/scan-information/subject_scans_info_Mindboggle101.tar.gz::"
            f"scans/NKI-TRT-20/NKI-TRT-20.phenotypic.csv row {number}; same archive::"
            f"scans/NKI-TRT-20/README_NKI-TRT-20.txt; {OFFICIAL_TRT}; {PRIMARY_NKI}"
        )
        note=(f"The {row['space']} row is one coordinate-space product of the single included Mindboggle acquisition. "
              "The source cohort is explicitly test-retest, but supplied evidence does not identify the included session, counterpart session, or temporal role.")
        lineage.append({
            "scan_id":row["scan_id"],"source_subject_id":source,"participant_group_id":group,
            "acquisition_session_identifier":"","scan_or_rescan_role":"unresolved",
            "repeat_acquisition_group":repeat_group,"repeat_acquisition_evidence":"confirmed_test_retest_design_counterpart_session_unidentified",
            "evidence_source":evidence_source,"exact_evidence_location":evidence_location,
            "resolution_status":"participant_and_repeat_group_resolved_acquisition_and_role_unresolved",
            "notes":note,"space":row["space"],"external_nki_session_evidence":ext_session,
        })
        q=qc_by_scan[row["scan_id"]]
        file_dup=q["mri_file_sha256"] in hash_indexes["mri_file_sha256"] or q["label_file_sha256"] in hash_indexes["label_file_sha256"]
        voxel_dup=q["mri_voxel_sha256"] in hash_indexes["mri_voxel_sha256"] or q["label_voxel_sha256"] in hash_indexes["label_voxel_sha256"]
        if row["space"]=="native":
            relationship=("confirmed_same_participant_as_nki_rs22_acquisition_relationship_unresolved" if rs_subjects else
                          "confirmed_subject_in_supplied_wider_nki_metadata" if ext else
                          "no_cross_cohort_subject_match_in_reviewed_local_metadata")
            overlap.append({
                "nki_trt_subject":subject,"source_subject_id":source,"participant_group_id":group,
                "nki_rs22_overlap_subjects":";".join(rs_subjects),"other_mindboggle_overlap_subjects":";".join(other_mb),
                "supplied_external_nki_metadata_match":"yes" if ext else "no",
                "external_nki_session_identifier":ext_session,
                "exact_file_duplicate_with_accepted_cohorts":"yes" if file_dup else "no",
                "exact_voxel_duplicate_with_accepted_cohorts":"yes" if voxel_dup else "no",
                "relationship_status":relationship,
                "evidence_source":"subject_sources_Mindboggle101; NKI-RS selected metadata; NKI.1-39.NumbersQC.csv; accepted cohort QC hashes; official NKI test-retest page",
                "exact_evidence_location":evidence_location,
                "notes":"Participant identity uses exact supplied source IDs. Lack of an exact voxel duplicate does not by itself resolve whether acquisitions differ.",
            })
        subject_issues=issue_by_subject.get(subject,[]); ids=sorted({x["affected_label_id"] for x in subject_issues},key=int)
        actions=sorted({x["required_action"] for x in subject_issues})
        item=dict(row); item.update({
            "participant_group_id":group,"acquisition_session_identifier":"","scan_rescan_role":"unresolved",
            "repeat_acquisition_group":repeat_group,"repeat_acquisition_evidence":"confirmed_test_retest_design_counterpart_session_unidentified",
            "lineage_resolution_status":"participant_and_repeat_group_resolved_acquisition_and_role_unresolved",
            "lineage_evidence_source":evidence_source,"lineage_evidence_location":evidence_location,
            "nki_rs22_overlap_subjects":";".join(rs_subjects),"external_nki_session_evidence":ext_session,
            "label_issue_review_status":"reviewed_issue_entries" if ids else "no_nki_trt20_issue_entry",
            "label_issue_metadata_ids":";".join(ids),"label_issue_action":";".join(actions) if actions else "no_action",
            "label_issue_evidence":"data/raw/mindboggle101/metadata/label-issues_201903.txt" if ids else "same file; no subject entry",
        }); updated.append(item)
    if len({r["participant_group_id"] for r in lineage})!=20 or len({r["repeat_acquisition_group"] for r in lineage})!=20:
        raise ValueError("Expected 20 participant and repeat groups")
    if len(overlap)!=20 or sum(bool(r["nki_rs22_overlap_subjects"]) for r in overlap)!=2:
        raise ValueError("Expected 20 overlap rows and two NKI-RS overlaps")
    additions=[f for f in updated[0] if f not in fields]
    write(LINEAGE,list(lineage[0]),lineage); write(ISSUES,list(issues[0]),issues)
    write(OVERLAP,list(overlap[0]),overlap); write(MANIFEST,fields+additions,updated)
    print("lineage_rows=40 participant_groups_confirmed=20 participant_groups_unresolved=0 repeat_groups_confirmed=20")
    print(f"nki_rs22_participant_overlaps=2 wider_nki_metadata_matches={sum(r['supplied_external_nki_metadata_match']=='yes' for r in overlap)} exact_cross_cohort_duplicates={sum(r['exact_file_duplicate_with_accepted_cohorts']=='yes' or r['exact_voxel_duplicate_with_accepted_cohorts']=='yes' for r in overlap)}")
    print(f"label_issue_rows={len(issues)} issue_subjects={len(issue_by_subject)} annotation_only={sum(r['required_action']=='annotation_only' for r in issues)} not_applicable={sum(r['required_action']=='not_applicable_to_canonical_DKT31' for r in issues)} exclusions=0 unresolved_actions=0")
    return 0


if __name__ == "__main__": raise SystemExit(main())
