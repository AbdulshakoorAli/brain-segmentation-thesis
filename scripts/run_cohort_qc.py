"""Run the accepted reusable QC engine for one standard cohort manifest."""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from brain_segmentation.qc import REQUIRED_CHECK_COLUMNS, annotate_duplicates, evaluate_pair, finalize_status  # noqa: E402


def read(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        return list(reader.fieldnames or []), list(reader)


def write(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
        writer.writeheader(); writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cohort", required=True)
    parser.add_argument("--expected-subjects", required=True, type=int)
    parser.add_argument("--output-prefix")
    args = parser.parse_args()
    slug = args.output_prefix or re.sub(r"[^a-z0-9]+", "_", args.cohort.lower()).strip("_")
    manifest = ROOT / f"data/derived/manifests/{slug}_scan_inventory.csv"
    qc_path = ROOT / f"data/derived/qc/{slug}_pair_qc.csv"
    failures_path = ROOT / f"data/derived/qc/{slug}_failures.csv"
    fields, rows = read(manifest)
    expected = args.expected_subjects * 2
    if len(rows) != expected or {r["cohort"] for r in rows} != {args.cohort}:
        raise ValueError(f"Expected {expected} rows for {args.cohort}")
    _, dictionary = read(ROOT / "data/derived/dictionaries/dkt_label_dictionary.csv")
    known = {int(r["original_label_id"]) for r in dictionary}
    if len(dictionary) != 62 or len(known) != 62:
        raise ValueError("Accepted DKT dictionary changed")
    qc_rows = []
    for source in rows:
        outcome = evaluate_pair(ROOT/source["mri_path"], ROOT/source["label_path"], source["space"], known)
        qc_rows.append({"scan_id":source["scan_id"],"participant_id":source["participant_id"],"cohort":source["cohort"],"space":source["space"],"mri_path":source["mri_path"],"label_path":source["label_path"],**outcome})
    annotate_duplicates(qc_rows)
    for row in qc_rows: finalize_status(row)
    preferred=["scan_id","participant_id","cohort","space","mri_path","label_path","validation_status","failed_checks","blocked_checks",*REQUIRED_CHECK_COLUMNS]
    all_fields={f for r in qc_rows for f in r}
    write(qc_path,preferred+sorted(all_fields-set(preferred)),qc_rows)
    failures=[]
    for row in qc_rows:
        for check in REQUIRED_CHECK_COLUMNS:
            if row.get(check) in {"failed","blocked"}:
                failures.append({"scan_id":row["scan_id"],"participant_id":row["participant_id"],"space":row["space"],"check":check,"status":row[check],"detail":row.get(check.removesuffix("_status")+"_error", ""),"unknown_label_ids":row.get("unknown_label_ids","")})
    write(failures_path,["scan_id","participant_id","space","check","status","detail","unknown_label_ids"],failures)
    by_scan={r["scan_id"]:r for r in qc_rows}
    derived=["mri_dimensions","label_dimensions","mri_voxel_spacing","label_voxel_spacing","mri_orientation","label_orientation","affine_match","label_ids_present","unknown_label_ids","validation_status"]
    updated=[]
    for source in rows:
        q=by_scan[source["scan_id"]]; item=dict(source)
        item.update({"pairing_status":q["validation_status"],"exclusion_reason":q["failed_checks"] or q["blocked_checks"],"mri_dimensions":q.get("mri_dimensions",""),"label_dimensions":q.get("label_dimensions",""),"mri_voxel_spacing":q.get("mri_voxel_spacing",""),"label_voxel_spacing":q.get("label_voxel_spacing",""),"mri_orientation":q.get("mri_orientation",""),"label_orientation":q.get("label_orientation",""),"affine_match":q.get("affine_status",""),"label_ids_present":q.get("label_ids",""),"unknown_label_ids":q.get("unknown_label_ids",""),"validation_status":q["validation_status"]})
        updated.append(item)
    write(manifest,fields+[f for f in derived if f not in fields],updated)
    unknown=sorted({int(x) for r in qc_rows for x in r.get("unknown_label_ids","").split(";") if x})
    print(f"pairs={len(qc_rows)} verified={sum(r['validation_status']=='verified' for r in qc_rows)} failed={sum(r['validation_status']=='failed' for r in qc_rows)} blocked={sum(r['validation_status']=='blocked' for r in qc_rows)}")
    print(f"failure_rows={len(failures)} unknown_label_ids={';'.join(map(str,unknown))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
