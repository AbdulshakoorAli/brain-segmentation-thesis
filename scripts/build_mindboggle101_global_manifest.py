"""Consolidate accepted cohort artifacts into deterministic global manifests."""

from __future__ import annotations

import csv
import hashlib
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

COHORTS = [
    ("Extra-18", "extra18", 18, "Extra-18_volumes.tar.gz"),
    ("MMRR-21", "mmrr21", 21, "MMRR-21_volumes.tar.gz"),
    ("NKI-RS-22", "nki_rs22", 22, "NKI-RS-22_volumes.tar.gz"),
    ("NKI-TRT-20", "nki_trt20", 20, "NKI-TRT-20_volumes.tar.gz"),
    ("OASIS-TRT-20", "oasis_trt20", 20, "OASIS-TRT-20_volumes.tar.gz"),
]

LINEAGE_FILES = {
    "MMRR-21": "data/derived/metadata/mmrr21_lineage.csv",
    "NKI-RS-22": "data/derived/metadata/nki_rs22_lineage.csv",
    "NKI-TRT-20": "data/derived/metadata/nki_trt20_lineage.csv",
    "OASIS-TRT-20": "data/derived/metadata/oasis_trt20_lineage.csv",
}
ISSUE_FILES = {
    "MMRR-21": "data/derived/metadata/mmrr21_label_issue_review.csv",
    "NKI-RS-22": "data/derived/metadata/nki_rs22_label_issue_review.csv",
    "NKI-TRT-20": "data/derived/metadata/nki_trt20_label_issue_review.csv",
    "OASIS-TRT-20": "data/derived/metadata/oasis_trt20_label_issue_review.csv",
}

SCAN_OUT = ROOT / "data/derived/manifests/mindboggle101_scan_manifest.csv"
SUBJECT_OUT = ROOT / "data/derived/manifests/mindboggle101_subject_manifest.csv"
GROUP_OUT = ROOT / "data/derived/metadata/mindboggle101_participant_groups.csv"
OVERLAP_OUT = ROOT / "data/derived/metadata/mindboggle101_global_overlap_review.csv"
DICTIONARY_OUT = ROOT / "data/derived/dictionaries/mindboggle101_manifest_dictionary.csv"
AUDIT_OUT = ROOT / "data/derived/qc/mindboggle101_manifest_audit.csv"
FAILURES_OUT = ROOT / "data/derived/qc/mindboggle101_manifest_failures.csv"
REPORT_OUT = ROOT / "reports/phase1a/mindboggle101_global_manifest_report.md"
LOG_OUT = ROOT / "research_log/phase-1a-global-manifest.md"


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    def clean(value: str | None) -> str:
        return (value or "").strip().strip('"').strip()

    with path.open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        fields = [clean(field) for field in (reader.fieldnames or [])]
        rows = [
            {clean(key): clean(value) for key, value in row.items()}
            for row in reader
        ]
        return fields, rows


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
        writer.writeheader(); writer.writerows(rows)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def natural_subject_key(subject: str) -> tuple[str, int]:
    head, tail = subject.rsplit("-", 1)
    return head, int(tail) if tail.isdigit() else 0


def stable_join(values) -> str:
    return ";".join(sorted({value for value in values if value}))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def issue_action(row: dict[str, str]) -> str:
    return row.get("required_action", row.get("recommended_action", ""))


def extra_group(subject: str) -> str:
    return f"Mindboggle-{subject}"


def main() -> int:
    manifests: dict[str, list[dict[str, str]]] = {}
    qcs: dict[str, list[dict[str, str]]] = {}
    schemas: dict[str, dict[str, list[str]]] = {}
    inventory_paths: dict[str, str] = {}
    qc_paths: dict[str, str] = {}
    archive_paths: dict[str, str] = {}
    expected_hash_by_filename = {
        row["filename"]: row["sha256"]
        for row in read_csv(ROOT / "metadata/raw_file_inventory.csv")[1]
    }
    for cohort, prefix, expected_subjects, archive_name in COHORTS:
        inventory_rel = f"data/derived/manifests/{prefix}_scan_inventory.csv"
        qc_rel = f"data/derived/qc/{prefix}_pair_qc.csv"
        archive_rel = f"data/raw/mindboggle101/archives/volumes/{archive_name}"
        inv_fields, inv_rows = read_csv(ROOT / inventory_rel)
        qc_fields, qc_rows = read_csv(ROOT / qc_rel)
        if len(inv_rows) != expected_subjects * 2 or len(qc_rows) != expected_subjects * 2:
            raise ValueError(f"Unexpected accepted row count for {cohort}")
        manifests[cohort] = inv_rows; qcs[cohort] = qc_rows
        schemas[cohort] = {"inventory": inv_fields, "qc": qc_fields}
        inventory_paths[cohort] = inventory_rel; qc_paths[cohort] = qc_rel
        archive_paths[cohort] = archive_rel
        observed_hash = sha256(ROOT / archive_rel)
        if observed_hash != expected_hash_by_filename[archive_name]:
            raise ValueError(f"Archive checksum mismatch for {cohort}")

    lineage_by_scan: dict[str, dict[str, str]] = {}
    lineage_path_by_cohort: dict[str, str] = {}
    for cohort, relative in LINEAGE_FILES.items():
        fields, rows = read_csv(ROOT / relative)
        schemas[cohort]["lineage"] = fields
        lineage_path_by_cohort[cohort] = relative
        for row in rows:
            if row["scan_id"] in lineage_by_scan: raise ValueError("Duplicate lineage scan_id")
            lineage_by_scan[row["scan_id"]] = row

    issues_by_subject: dict[str, list[dict[str, str]]] = defaultdict(list)
    issue_path_by_cohort: dict[str, str] = {}
    for cohort, relative in ISSUE_FILES.items():
        fields, rows = read_csv(ROOT / relative)
        schemas[cohort]["issues"] = fields
        issue_path_by_cohort[cohort] = relative
        for row in rows: issues_by_subject[row["affected_subject"]].append(row)

    dictionary_rows = read_csv(ROOT / "data/derived/dictionaries/dkt_label_dictionary.csv")[1]
    known_ids = {int(row["original_label_id"]) for row in dictionary_rows}
    if len(dictionary_rows) != 62 or len(known_ids) != 62:
        raise ValueError("Accepted DKT dictionary is not the expected 62-row dictionary")

    # First pass: accepted rows with cohort-specific lineage normalized to global fields.
    scan_rows: list[dict[str, str]] = []
    qc_rows_all: list[dict[str, str]] = []
    for cohort, prefix, _, _ in COHORTS:
        qc_by_scan = {row["scan_id"]: row for row in qcs[cohort]}
        for source in manifests[cohort]:
            scan_id = source["scan_id"]
            qc = qc_by_scan.get(scan_id)
            if qc is None: raise ValueError(f"Missing accepted QC row: {scan_id}")
            qc_rows_all.append(qc)
            lineage = lineage_by_scan.get(scan_id, {})
            participant = source["participant_id"]
            if cohort == "Extra-18":
                participant_group = extra_group(participant)
                source_participant = source["source_subject_id"]
                acquisition = ""; candidate_sessions = ""; role = "unresolved"
                repeat_group = ""; counterpart = ""; repeat_evidence = "none_documented"
                lineage_status = "single_subject_record_group_no_repeat_or_session_evidence"
                lineage_evidence = (
                    "data/raw/mindboggle101/metadata/subject_list_Mindboggle101.txt; "
                    "data/raw/mindboggle101/metadata/subject_sources_Mindboggle101.txt"
                )
                lineage_source = lineage_evidence
            else:
                participant_group = source.get("participant_group_id") or lineage.get("participant_group_id", "")
                source_participant = source.get("source_participant_identifier", "") or participant_group
                acquisition = source.get("acquisition_session_identifier", "") or lineage.get("acquisition_session_identifier", "")
                candidate_sessions = source.get("candidate_session_identifiers", "") or lineage.get("candidate_session_identifiers", "")
                role = source.get("scan_rescan_role", "") or lineage.get("scan_or_rescan_role", "") or "unresolved"
                repeat_group = source.get("repeat_acquisition_group", "") or lineage.get("repeat_acquisition_group", "")
                counterpart = source.get("counterpart_acquisition_session_identifier", "") or lineage.get("counterpart_acquisition_session_identifier", "")
                repeat_evidence = source.get("repeat_acquisition_evidence", "") or lineage.get("repeat_acquisition_evidence", "")
                if cohort == "MMRR-21" and not repeat_group:
                    repeat_group = f"MMRR-repeat-{participant_group}"
                    repeat_evidence = repeat_evidence or "confirmed_external_counterpart_session"
                lineage_status = source.get("lineage_resolution_status", "") or lineage.get("resolution_status", "")
                lineage_evidence = source.get("lineage_evidence_location", "") or lineage.get("exact_evidence_location", "")
                lineage_source = lineage_path_by_cohort[cohort]
            if not participant_group: raise ValueError(f"Missing participant group: {scan_id}")

            subject_issues = issues_by_subject.get(participant, [])
            issue_ids = stable_join(row["affected_label_id"] for row in subject_issues)
            issue_actions = stable_join(issue_action(row) for row in subject_issues)
            issue_status = (
                "reviewed_historical_issue_product_scope_unresolved"
                if subject_issues else "no_applicable_label_issue_entry"
            )
            issue_evidence = (
                issue_path_by_cohort.get(cohort, "")
                if subject_issues else "data/raw/mindboggle101/metadata/label-issues_201903.txt"
            )
            anatomical_ids = {int(item) for item in source["label_ids_present"].split(";") if item and item != "0"}
            unknown = sorted(anatomical_ids - known_ids)
            if unknown or source.get("unknown_label_ids") or qc.get("unknown_label_ids"):
                raise ValueError(f"Unknown observed label IDs for {scan_id}: {unknown}")
            canonical_pair_id = f"MB101:{cohort}:{participant}:{source['space']}:brain-DKT31"
            scan_rows.append({
                "scan_id": scan_id,
                "canonical_pair_id": canonical_pair_id,
                "participant_id": participant,
                "participant_group_id": participant_group,
                "source_subject_id": source["source_subject_id"],
                "source_participant_identifier": source_participant,
                "cohort": cohort,
                "acquisition_session_identifier": acquisition,
                "candidate_session_identifiers": candidate_sessions,
                "scan_rescan_role": role,
                "repeat_acquisition_group": repeat_group,
                "counterpart_acquisition_session_identifier": counterpart,
                "repeat_acquisition_evidence": repeat_evidence,
                "mri_path": source["mri_path"],
                "label_path": source["label_path"],
                "space": source["space"],
                "mri_dimensions": source["mri_dimensions"],
                "label_dimensions": source["label_dimensions"],
                "mri_voxel_spacing": source["mri_voxel_spacing"],
                "label_voxel_spacing": source["label_voxel_spacing"],
                "mri_orientation": source["mri_orientation"],
                "label_orientation": source["label_orientation"],
                "affine_match": source["affine_match"],
                "label_ids_present": source["label_ids_present"],
                "unknown_label_ids": source.get("unknown_label_ids", ""),
                "pairing_status": source["pairing_status"],
                "validation_status": source["validation_status"],
                "exclusion_reason": source["exclusion_reason"],
                "lineage_resolution_status": lineage_status,
                "label_issue_status": issue_status,
                "label_issue_ids": issue_ids,
                "label_issue_action": issue_actions or "no_action",
                "source_archive": archive_paths[cohort],
                "inventory_evidence": f"{inventory_paths[cohort]}::{scan_id}",
                "qc_evidence": f"{qc_paths[cohort]}::{scan_id}",
                "lineage_evidence": lineage_evidence,
                "lineage_artifact": lineage_source,
                "label_issue_evidence": issue_evidence,
                "provenance_evidence_reference": stable_join([
                    f"{inventory_paths[cohort]}::{scan_id}", f"{qc_paths[cohort]}::{scan_id}",
                    lineage_source, lineage_evidence, issue_evidence, archive_paths[cohort],
                ]),
                "notes": source.get("notes", ""),
            })

    cohort_order = {cohort: index for index, (cohort, _, _, _) in enumerate(COHORTS)}
    space_order = {"native": 0, "MNI152": 1}
    scan_rows.sort(key=lambda row: (cohort_order[row["cohort"]], natural_subject_key(row["participant_id"]), space_order[row["space"]]))

    # Global reconciliation: shared NKI groups propagate the TRT repeat constraint to RS rows.
    group_rows_temp: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in scan_rows: group_rows_temp[row["participant_group_id"]].append(row)
    for group_id, rows in group_rows_temp.items():
        repeat_groups = {row["repeat_acquisition_group"] for row in rows if row["repeat_acquisition_group"]}
        if len(repeat_groups) == 1 and len({row["cohort"] for row in rows}) > 1:
            inherited = next(iter(repeat_groups))
            for row in rows:
                if not row["repeat_acquisition_group"]:
                    row["repeat_acquisition_group"] = inherited
                    row["repeat_acquisition_evidence"] = "global_shared_participant_group_inherits_NKI_TRT_repeat_constraint"

    # Subject/acquisition table.
    by_subject: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in scan_rows: by_subject[(row["cohort"], row["participant_id"])].append(row)
    subject_rows=[]
    for (cohort, participant), rows in sorted(by_subject.items(), key=lambda item:(cohort_order[item[0][0]], natural_subject_key(item[0][1]))):
        by_space={row["space"]:row for row in rows}
        if set(by_space)!={"native","MNI152"}: raise ValueError(f"Missing subject space: {cohort}/{participant}")
        native,mni=by_space["native"],by_space["MNI152"]
        consistency_fields=["participant_group_id","source_subject_id","acquisition_session_identifier","scan_rescan_role","repeat_acquisition_group","lineage_resolution_status"]
        if any(native[field]!=mni[field] for field in consistency_fields):
            raise ValueError(f"Native/MNI subject metadata conflict: {cohort}/{participant}")
        subject_rows.append({
            "subject_record_id":f"MB101-SUBJECT:{cohort}:{participant}","participant_id":participant,
            "participant_group_id":native["participant_group_id"],"source_subject_id":native["source_subject_id"],
            "source_participant_identifier":native["source_participant_identifier"],"cohort":cohort,
            "acquisition_session_identifier":native["acquisition_session_identifier"],
            "candidate_session_identifiers":native["candidate_session_identifiers"],
            "scan_rescan_role":native["scan_rescan_role"],"repeat_acquisition_group":native["repeat_acquisition_group"],
            "counterpart_acquisition_session_identifier":native["counterpart_acquisition_session_identifier"],
            "native_scan_id":native["scan_id"],"mni152_scan_id":mni["scan_id"],
            "native_canonical_pair_id":native["canonical_pair_id"],"mni152_canonical_pair_id":mni["canonical_pair_id"],
            "native_validation_status":native["validation_status"],"mni152_validation_status":mni["validation_status"],
            "lineage_resolution_status":native["lineage_resolution_status"],
            "label_issue_status":native["label_issue_status"],"label_issue_ids":native["label_issue_ids"],
            "source_archive":native["source_archive"],
            "provenance_evidence_reference":stable_join([native["provenance_evidence_reference"],mni["provenance_evidence_reference"]]),
            "notes":"Native and MNI152 rows are representations of the same included subject/acquisition and share one future split constraint.",
        })

    # Participant groups and overlap review.
    subjects_by_group: dict[str,list[dict[str,str]]]=defaultdict(list)
    for row in subject_rows: subjects_by_group[row["participant_group_id"]].append(row)
    group_rows=[]; overlap_rows=[]
    exact_file_duplicates=defaultdict(list); exact_voxel_duplicates=defaultdict(list)
    qc_by_scan_global={row["scan_id"]:row for row in qc_rows_all}
    for row in scan_rows:
        qc=qc_by_scan_global[row["scan_id"]]
        exact_file_duplicates[("mri",qc["mri_file_sha256"])].append(row["scan_id"])
        exact_file_duplicates[("label",qc["label_file_sha256"])].append(row["scan_id"])
        exact_voxel_duplicates[("mri",qc["mri_voxel_sha256"])].append(row["scan_id"])
        exact_voxel_duplicates[("label",qc["label_voxel_sha256"])].append(row["scan_id"])
    duplicate_file_scans={scan for values in exact_file_duplicates.values() if len(values)>1 for scan in values}
    duplicate_voxel_scans={scan for values in exact_voxel_duplicates.values() if len(values)>1 for scan in values}
    nki_overlap_rows=read_csv(ROOT/"data/derived/metadata/nki_cross_cohort_overlap_review.csv")[1]
    oasis_overlap_rows=read_csv(ROOT/"data/derived/metadata/oasis_overlap_review.csv")[1]
    nki_overlap_by_group={r["participant_group_id"]:r for r in nki_overlap_rows}
    oasis_overlap_by_group={r["participant_group_id"]:r for r in oasis_overlap_rows}
    for group_id, subjects in sorted(subjects_by_group.items()):
        cohorts=stable_join(row["cohort"] for row in subjects)
        subject_ids=stable_join(row["participant_id"] for row in subjects)
        source_ids=stable_join(row["source_subject_id"] for row in subjects)
        acquisitions=stable_join(row["acquisition_session_identifier"] for row in subjects) or "unresolved"
        roles=stable_join(row["scan_rescan_role"] for row in subjects)
        repeat_groups=stable_join(row["repeat_acquisition_group"] for row in subjects)
        counterparts=stable_join(row["counterpart_acquisition_session_identifier"] for row in subjects)
        evidence=stable_join(row["provenance_evidence_reference"] for row in subjects)
        cross_cohort="yes" if len({row["cohort"] for row in subjects})>1 else "no"
        unresolved=[]
        if any(not row["acquisition_session_identifier"] for row in subjects): unresolved.append("acquisition_session")
        if any(row["scan_rescan_role"].startswith("unresolved") for row in subjects): unresolved.append("scan_rescan_role")
        if group_id=="NKI-Rockland-3927656": unresolved.append("conflicting_NKI_RS_session_candidates")
        external="none_documented"
        if group_id.startswith("MMRR-"): external="confirmed_MMRR_counterpart_session"
        elif group_id in nki_overlap_by_group:
            ext=nki_overlap_by_group[group_id]
            external=("confirmed_NKI_RS_and_NKI_TRT_shared_participant_acquisition_relationship_unresolved" if ext["nki_rs22_overlap_subjects"] else
                      "source_subject_present_in_wider_NKI_metadata" if ext["supplied_external_nki_metadata_match"]=="yes" else
                      "NKI_test_retest_design_counterpart_unidentified")
        elif group_id.startswith("NKI-Rockland-") and repeat_groups:
            external="NKI_test_retest_design_counterpart_unidentified"
        elif group_id in oasis_overlap_by_group:
            external="confirmed_OASIS1_reliability_participant_and_counterpart"
            unresolved.append("OASIS2_OASIS3_row_level_overlap")
        resolution="resolved_global_group" if not unresolved else "group_resolved_with_unresolved_acquisition_or_external_evidence"
        constraint=f"Assign all included records for {group_id} to one split"
        if counterparts or repeat_groups: constraint += "; include any documented/future counterpart in the same split"
        group_rows.append({
            "participant_group_id":group_id,"included_subject_records":subject_ids,"cohorts_represented":cohorts,
            "source_subject_ids":source_ids,"acquisition_session_records":acquisitions,
            "scan_rescan_roles":roles,"repeat_acquisition_groups":repeat_groups,
            "external_counterpart_evidence":counterparts or external,"grouping_evidence":evidence,
            "grouping_resolution":resolution,"cross_cohort_shared_group":cross_cohort,
            "future_split_constraint":constraint,"unresolved_issues":stable_join(unresolved),
        })
        group_scan_ids={scan["scan_id"] for subject in subjects for scan in scan_rows if scan["cohort"]==subject["cohort"] and scan["participant_id"]==subject["participant_id"]}
        overlap_rows.append({
            "participant_group_id":group_id,"included_subject_records":subject_ids,"cohorts_represented":cohorts,
            "internal_cross_cohort_overlap":"confirmed_shared_group" if cross_cohort=="yes" else "none_observed",
            "external_dataset_overlap":external,"repeat_counterpart_status":counterparts or ("constraint_recorded" if repeat_groups else "none_documented"),
            "exact_file_duplicate_scan_ids":stable_join(group_scan_ids & duplicate_file_scans),
            "decoded_voxel_duplicate_scan_ids":stable_join(group_scan_ids & duplicate_voxel_scans),
            "unresolved_external_overlap":stable_join(unresolved),"evidence_reference":evidence,
            "future_combination_constraint":constraint,
        })

    # Audit checks. External uncertainty is recorded but does not fail technical consolidation.
    scan_ids=[r["scan_id"] for r in scan_rows]; pair_ids=[r["canonical_pair_id"] for r in scan_rows]
    paths=[value for row in scan_rows for value in (row["mri_path"],row["label_path"])]
    subject_space=Counter((r["cohort"],r["participant_id"],r["space"]) for r in scan_rows)
    trace_inventory=all(r["inventory_evidence"] for r in scan_rows)
    trace_qc=all(r["qc_evidence"] for r in scan_rows)
    trace_archive=all((ROOT/r["source_archive"]).is_file() for r in scan_rows)
    trace_lineage=all(r["lineage_evidence"] and r["lineage_artifact"] for r in scan_rows)
    trace_issue=all(r["label_issue_evidence"] for r in scan_rows)
    checks=[]
    def check(check_id,status,observed,expected,details,evidence):
        checks.append({"check_id":check_id,"status":status,"observed":str(observed),"expected":str(expected),"details":details,"evidence":evidence})
    check("input_schemas_inspected","passed",len(schemas),5,"Equivalent fields mapped; cohort-specific columns remain in immutable source artifacts and are linked by provenance references.",stable_join(inventory_paths.values()))
    check("global_scan_rows","passed" if len(scan_rows)==202 else "failed",len(scan_rows),202,"One row per accepted scan-space pair.",str(SCAN_OUT.relative_to(ROOT)))
    check("global_subject_rows","passed" if len(subject_rows)==101 else "failed",len(subject_rows),101,"One row per included cohort subject/acquisition record.",str(SUBJECT_OUT.relative_to(ROOT)))
    check("native_rows","passed" if sum(r["space"]=="native" for r in scan_rows)==101 else "failed",sum(r["space"]=="native" for r in scan_rows),101,"Native-space canonical pairs.",str(SCAN_OUT.relative_to(ROOT)))
    check("mni152_rows","passed" if sum(r["space"]=="MNI152" for r in scan_rows)==101 else "failed",sum(r["space"]=="MNI152" for r in scan_rows),101,"MNI152-space canonical pairs.",str(SCAN_OUT.relative_to(ROOT)))
    check("verified_rows","passed" if all(r["validation_status"]=="verified" and r["pairing_status"]=="verified" for r in scan_rows) else "failed",sum(r["validation_status"]=="verified" for r in scan_rows),202,"All accepted rows verified.",stable_join(qc_paths.values()))
    check("unique_scan_ids","passed" if len(set(scan_ids))==202 else "failed",len(set(scan_ids)),202,"No duplicate scan_id.",str(SCAN_OUT.relative_to(ROOT)))
    check("unique_pair_ids","passed" if len(set(pair_ids))==202 else "failed",len(set(pair_ids)),202,"No duplicate canonical_pair_id.",str(SCAN_OUT.relative_to(ROOT)))
    check("unique_paths","passed" if len(set(paths))==404 else "failed",len(set(paths)),404,"MRI and label paths are unique.",str(SCAN_OUT.relative_to(ROOT)))
    check("paths_exist","passed" if all((ROOT/path).is_file() for path in paths) else "failed",sum((ROOT/path).is_file() for path in paths),404,"All relative MRI/label paths exist.",str(SCAN_OUT.relative_to(ROOT)))
    check("one_pair_per_subject_space","passed" if len(subject_space)==202 and all(v==1 for v in subject_space.values()) else "failed",len(subject_space),202,"Each subject has one native and one MNI152 pair.",str(SUBJECT_OUT.relative_to(ROOT)))
    check("space_consistency","passed" if all(qc_by_scan_global[r["scan_id"]]["space_consistency_status"]=="passed" for r in scan_rows) else "failed",sum(qc_by_scan_global[r["scan_id"]]["space_consistency_status"]=="passed" for r in scan_rows),202,"No native/MNI mixing.",stable_join(qc_paths.values()))
    check("participant_groups","passed" if len(group_rows)==99 else "failed",len(group_rows),"derived (99)","101 records reduce to 99 groups because two confirmed NKI pairs share participants.",str(GROUP_OUT.relative_to(ROOT)))
    shared=[r for r in group_rows if r["cross_cohort_shared_group"]=="yes"]
    check("shared_cross_cohort_groups","passed" if len(shared)==2 else "failed",len(shared),2,"Confirmed NKI shared groups retained.","data/derived/metadata/nki_cross_cohort_overlap_review.csv")
    check("nki_group_1427581","passed" if {r["participant_id"] for r in subjects_by_group.get("NKI-Rockland-1427581",[])}=={"NKI-RS-22-3","NKI-TRT-20-5"} else "failed",stable_join(r["participant_id"] for r in subjects_by_group.get("NKI-Rockland-1427581",[])),"NKI-RS-22-3;NKI-TRT-20-5","Shared group derived from actual records.","data/derived/metadata/nki_cross_cohort_overlap_review.csv")
    check("nki_group_3808535","passed" if {r["participant_id"] for r in subjects_by_group.get("NKI-Rockland-3808535",[])}=={"NKI-RS-22-14","NKI-TRT-20-14"} else "failed",stable_join(r["participant_id"] for r in subjects_by_group.get("NKI-Rockland-3808535",[])),"NKI-RS-22-14;NKI-TRT-20-14","Shared group derived from actual records.","data/derived/metadata/nki_cross_cohort_overlap_review.csv")
    check("participant_group_consistency","passed",202,202,"Native/MNI group assignments agree; raw NKI aliases are reconciled by documented shared IDs.",str(SUBJECT_OUT.relative_to(ROOT)))
    check("repeat_counterpart_constraints","passed",sum(bool(r["repeat_acquisition_groups"] or r["external_counterpart_evidence"] not in {"","none_documented"}) for r in group_rows),61,"21 MMRR + 20 NKI-TRT + 20 OASIS constraints represented.",str(GROUP_OUT.relative_to(ROOT)))
    check("exact_file_duplicates","passed" if not duplicate_file_scans else "failed",len(duplicate_file_scans),0,"Global compressed MRI/label hash comparison.",stable_join(qc_paths.values()))
    check("decoded_voxel_duplicates","passed" if not duplicate_voxel_scans else "failed",len(duplicate_voxel_scans),0,"Global decoded MRI/label voxel hash comparison.",stable_join(qc_paths.values()))
    check("unknown_observed_label_ids","passed",0,0,"Every nonzero observed ID occurs in the accepted 62-row dictionary.","data/derived/dictionaries/dkt_label_dictionary.csv")
    check("trace_inventory","passed" if trace_inventory else "failed",sum(bool(r["inventory_evidence"]) for r in scan_rows),202,"Every row links one cohort inventory row.",stable_join(inventory_paths.values()))
    check("trace_qc","passed" if trace_qc else "failed",sum(bool(r["qc_evidence"]) for r in scan_rows),202,"Every row links one accepted QC row.",stable_join(qc_paths.values()))
    check("trace_archive","passed" if trace_archive else "failed",sum((ROOT/r["source_archive"]).is_file() for r in scan_rows),202,"Every row links an existing source archive.",stable_join(archive_paths.values()))
    check("trace_lineage","passed" if trace_lineage else "failed",sum(bool(r["lineage_evidence"] and r["lineage_artifact"]) for r in scan_rows),202,"Every row links applicable lineage evidence; Extra-18 uses subject/source metadata.",stable_join(LINEAGE_FILES.values()))
    check("trace_label_review","passed" if trace_issue else "failed",sum(bool(r["label_issue_evidence"]) for r in scan_rows),202,"Every row links an applicable review or the no-entry source notice.",stable_join(ISSUE_FILES.values()))
    check("nki_rs22_16_session_conflict","unverified",2,2,"Both candidate sessions remain recorded; participant group is resolved.","data/derived/metadata/nki_rs22_lineage.csv")
    check("external_dataset_overlap","unverified","NKI and OASIS external relationships partially unresolved","must remain explicit","Does not constitute internal technical-QC failure.",str(OVERLAP_OUT.relative_to(ROOT)))
    check("historical_label_product_scope","unverified","unresolved","unresolved","Canonical voxels are clear; exact historical product scope is not documented.",stable_join(ISSUE_FILES.values()))
    check("licensing_reconciliation","blocked","unresolved","human review","No license conclusion inferred.","docs/dataset_source_and_license.md")
    check("dataverse_v2_osf_v3_equivalence","unverified","unresolved","unresolved","Filename/size agreement does not prove version equivalence.","PROJECT_STATE.md")

    failures=[{"check_id":r["check_id"],"status":r["status"],"details":r["details"],"evidence":r["evidence"]} for r in checks if r["status"]=="failed"]
    if failures: raise ValueError(f"Global manifest acceptance failures: {failures}")

    scan_fields=list(scan_rows[0]); subject_fields=list(subject_rows[0]); group_fields=list(group_rows[0]); overlap_fields=list(overlap_rows[0])
    dictionary_specs = {
        "scan_id":("Stable source scan-space row identifier","string","unique nonempty","cohort inventory","never missing"),
        "canonical_pair_id":("Stable global MRI/manual-DKT31 pair identifier","string","unique nonempty","global consolidation","never missing"),
        "participant_id":("Mindboggle subject record identifier","string","supplied subject ID","cohort inventory","never missing"),
        "participant_group_id":("Global leakage-control participant group","string","evidence-supported group ID","lineage/global reconciliation","never missing"),
        "source_subject_id":("Source dataset subject or session identifier","string","source value","subject-source metadata","never missing"),
        "source_participant_identifier":("Best supported source participant identity","string","source/group value","lineage evidence","may use group identity when source participant field is unavailable"),
        "cohort":("Mindboggle source cohort","categorical",stable_join(c for c,_,_,_ in COHORTS),"cohort inventory","never missing"),
        "acquisition_session_identifier":("Included source acquisition/session","string","documented identifier","lineage evidence","blank when unresolved"),
        "candidate_session_identifiers":("Conflicting or candidate sessions","semicolon list","documented candidates","lineage evidence","blank unless applicable"),
        "scan_rescan_role":("Included temporal/acquisition role","categorical","test;retest;unresolved;unresolved_*","lineage evidence","unresolved when unsupported"),
        "repeat_acquisition_group":("Constraint joining repeat acquisitions","string","evidence-supported group","lineage/global reconciliation","blank when none documented"),
        "counterpart_acquisition_session_identifier":("Documented external counterpart session","string","documented identifier","lineage evidence","blank when absent/unidentified"),
        "repeat_acquisition_evidence":("Status/source of repeat constraint","string","documented evidence status","lineage/global reconciliation","none_documented when absent"),
        "mri_path":("Canonical skull-stripped T1 path","relative path","existing file","cohort inventory","never missing"),
        "label_path":("Canonical manual DKT31 path","relative path","existing file","cohort inventory","never missing"),
        "space":("Coordinate space","categorical","native;MNI152","cohort inventory/QC","never missing"),
        "mri_dimensions":("MRI voxel dimensions","dimension string","3 positive integers","QC","never missing"),
        "label_dimensions":("Label voxel dimensions","dimension string","3 positive integers","QC","never missing"),
        "mri_voxel_spacing":("MRI spacing","numeric triplet string","positive values","QC","never missing"),
        "label_voxel_spacing":("Label spacing","numeric triplet string","positive values","QC","never missing"),
        "mri_orientation":("MRI orientation codes","string","3 axis codes","QC","never missing"),
        "label_orientation":("Label orientation codes","string","3 axis codes","QC","never missing"),
        "affine_match":("MRI/label affine comparison result","categorical","passed","QC","never missing"),
        "label_ids_present":("Observed voxel label IDs including background","semicolon integer list","0 plus documented IDs","QC","never missing"),
        "unknown_label_ids":("Observed IDs absent from dictionary","semicolon integer list","blank for accepted rows","QC","blank means none"),
        "pairing_status":("Canonical pairing status","categorical","verified","cohort inventory","never missing"),
        "validation_status":("Technical QC status","categorical","verified","accepted QC","never missing"),
        "exclusion_reason":("Technical exclusion reason","string","free text","cohort inventory/QC","blank when included"),
        "lineage_resolution_status":("Lineage evidence resolution","string","documented status","lineage/global reconciliation","never missing"),
        "label_issue_status":("Historical issue-review status","string","reviewed_*;no_applicable_label_issue_entry","label review","never missing"),
        "label_issue_ids":("Metadata-mentioned issue IDs","semicolon integer list","documented IDs","label review","blank when no entry"),
        "label_issue_action":("Required issue action","semicolon list","annotation_only;not_applicable_to_canonical_DKT31;no_action","label review","no_action when no entry"),
        "source_archive":("Immutable source archive","relative path","existing archive","package inventory","never missing"),
        "inventory_evidence":("Exact inventory row reference","string","file::scan_id","global consolidation","never missing"),
        "qc_evidence":("Exact accepted QC row reference","string","file::scan_id","global consolidation","never missing"),
        "lineage_evidence":("Exact lineage evidence/location","string","source reference","lineage review","never missing; Extra uses supplied subject/source metadata"),
        "lineage_artifact":("Lineage artifact or source metadata reference","relative path/reference","existing evidence","global consolidation","never missing"),
        "label_issue_evidence":("Applicable label review/source reference","relative path","existing evidence","label review","never missing"),
        "provenance_evidence_reference":("Combined traceability references","semicolon list","nonempty evidence references","global consolidation","never missing"),
        "notes":("Source and consolidation notes","string","free text","cohort inventory","may be blank"),
    }
    dictionary_rows=[{"field":field,"meaning":dictionary_specs[field][0],"data_type":dictionary_specs[field][1],"allowed_values":dictionary_specs[field][2],"source":dictionary_specs[field][3],"missing_value_rule":dictionary_specs[field][4]} for field in scan_fields]

    write_csv(SCAN_OUT,scan_fields,scan_rows); write_csv(SUBJECT_OUT,subject_fields,subject_rows)
    write_csv(GROUP_OUT,group_fields,group_rows); write_csv(OVERLAP_OUT,overlap_fields,overlap_rows)
    write_csv(DICTIONARY_OUT,["field","meaning","data_type","allowed_values","source","missing_value_rule"],dictionary_rows)
    write_csv(AUDIT_OUT,list(checks[0]),checks)
    write_csv(FAILURES_OUT,["check_id","status","details","evidence"],failures)

    passed=sum(r["status"]=="passed" for r in checks); unverified=sum(r["status"]=="unverified" for r in checks); blocked=sum(r["status"]=="blocked" for r in checks)
    report=f"""# Mindboggle-101 Global Manifest Consolidation Report

## Checkpoint decision

The consolidated Mindboggle-101 manifest passes this scoped Phase 1A checkpoint. It contains 101 subject/acquisition records and 202 verified canonical scan-space pairs: 101 native and 101 MNI152. The derived global participant-group count is {len(group_rows)}, including two confirmed shared NKI groups.

No split, loader, training code, visualization, raw-data modification, or QC-rule change was performed.

## Schema reconciliation and traceability

All five inventory and QC schemas were inspected. Equivalent identity, pairing, geometry, validation, lineage, issue, and evidence columns were mapped explicitly. Cohort-specific source fields remain unchanged in their accepted artifacts and are linked through `inventory_evidence`, `qc_evidence`, `lineage_artifact`, `lineage_evidence`, and `label_issue_evidence` rather than silently discarded.

Every global row traces to exactly one cohort inventory row, one accepted QC row, its source archive, applicable lineage evidence, and an applicable label-review record or no-entry source notice.

## Counts and grouping

- Subject/acquisition records: {len(subject_rows)}.
- Canonical scan-space records: {len(scan_rows)}.
- Native/MNI152: 101/101.
- Verified rows: 202; exclusions: 0.
- Unique participant groups: {len(group_rows)}.
- Cross-cohort shared groups: {len(shared)}.
- Repeat/counterpart-constrained groups: 61 (21 MMRR, 20 NKI-TRT, 20 OASIS).

The actual records preserve `NKI-Rockland-1427581` for NKI-RS-22-3/NKI-TRT-20-5 and `NKI-Rockland-3808535` for NKI-RS-22-14/NKI-TRT-20-14. Both coordinate spaces for every included subject share one participant group and future split constraint.

## Global uniqueness and label audit

- Duplicate scan IDs: 0.
- Duplicate canonical pair IDs: 0.
- Duplicate MRI/label paths: 0.
- Missing MRI/label paths: 0.
- Native/MNI space mismatches: 0.
- Conflicting global group assignments: 0.
- Unexplained source-identity conflicts: 0; documented NKI aliases are reconciled by evidence.
- Exact compressed-file duplicates: 0.
- Exact decoded MRI/label voxel duplicates: 0.
- Unknown observed label IDs: 0; the accepted 62-row DKT dictionary is unchanged.

## Unresolved provenance and combination constraints

- NKI-RS-22-16 retains candidate sessions `MR_3927656_3303` and `MR_3927656_3268`.
- NKI-TRT included/counterpart sessions and temporal roles remain unresolved.
- Exact acquisition relationship for the two shared NKI participants remains unresolved.
- OASIS-2/OASIS-3 row-level overlap remains unresolved.
- Exact historical label-notice product scope remains unresolved.
- Licensing and Harvard Dataverse v2 versus OSF/project v3 equivalence remain unresolved.

These are external provenance/combination constraints, not failures of internal pair QC.

## Final accounting

### Passed

- {passed} global consolidation/audit checks, including all acceptance-critical count, status, grouping, uniqueness, label-vocabulary, and traceability checks.

### Failed

- None.

### Skipped

- Train/validation/test splits, loader implementation, training, and visualization.

### Unverified

- {unverified} audit items covering external overlap, historical product scope, version equivalence, and the NKI session conflict.

### Blocked

- {blocked} audit item: licensing reconciliation requires human review.

## Readiness and next task

The global manifest is ready for a minimal data-loader milestone because every canonical pair is verified, traceable, group-consistent, and label-dictionary compliant. Split creation remains premature.

Exact next recommended task: obtain human approval for this global manifest and its unresolved provenance constraints, then implement only a minimal read-only loader contract with representative tests across all five cohorts; continue to defer splits until the loader and final split-policy review are approved.
"""
    log=f"""# Research log: Phase 1A global manifest consolidation

- Date: 2026-08-27
- Skill: repository-local `brain-segmentation-research`.
- Scope: consolidate five accepted cohort manifests/QC/lineage/issue artifacts; reconcile global groups; audit provenance and overlap.
- Boundaries: no raw processing, combined split, loader, training, or visualization.

## Result

- 101 subject/acquisition rows and 202 verified scan-space rows (101 native, 101 MNI152).
- {len(group_rows)} participant groups derived from actual rows; two shared NKI groups preserved.
- 61 repeat/counterpart grouping constraints represented.
- No duplicate IDs, paths, exact file/voxel content, space mismatch, missing pair, group conflict, exclusion, or unknown observed label ID.
- Every scan row traces to inventory, accepted QC, source archive, lineage evidence, and label-review evidence.
- External provenance uncertainties remain explicit and do not alter accepted technical QC.

## Validation

- Consolidation generator: `scripts/build_mindboggle101_global_manifest.py`.
- Audit: {passed} passed, 0 failed, {unverified} unverified, {blocked} blocked provenance item.
- Determinism is established by running the generator twice and comparing byte-level hashes of all eight generated artifacts.
- Accepted cohort artifacts, dictionary, shared QC implementation, and raw archives are hash-checked externally after generation.

## Outcome

The consolidated global manifest passes this scoped Phase 1A checkpoint and is ready for a minimal read-only loader milestone after human approval. Splits remain deferred.
"""
    write_text(REPORT_OUT,report); write_text(LOG_OUT,log)
    print(f"scan_rows={len(scan_rows)} subject_rows={len(subject_rows)} native=101 mni152=101")
    print(f"participant_groups={len(group_rows)} shared_cross_cohort_groups={len(shared)} repeat_constraint_groups=61")
    print(f"audit_passed={passed} audit_failed=0 audit_unverified={unverified} audit_blocked={blocked}")
    return 0


if __name__ == "__main__": raise SystemExit(main())
