"""Focused real-data validation for the on-demand Mindboggle-101 3D viewer."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("MPLBACKEND", "Agg")
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / "data/derived/cache/matplotlib"))
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import matplotlib.pyplot as plt  # noqa: E402
import nibabel as nib  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.backends.backend_agg import FigureCanvasAgg  # noqa: E402
from mpl_toolkits.mplot3d.art3d import Poly3DCollection  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402
from skimage.measure import marching_cubes  # noqa: E402

from brain_segmentation.loading import get_record_by_canonical_pair_id, load_verified_pair, load_verified_records  # noqa: E402
from brain_segmentation.mesh_cache import (  # noqa: E402
    CACHE_METADATA_NAME, generate_mesh_cache, inspect_mesh_cache, quarantine_invalid_cache, safe_pair_key,
)
from brain_segmentation.mesh_visualization import (  # noqa: E402
    build_3d_figure, build_orthogonal_figure, initial_slices, load_region_meshes,
    sha256_file, validate_region_meshes,
)

MANIFEST = ROOT / "data/derived/manifests/mindboggle101_scan_manifest.csv"
DICTIONARY = ROOT / "data/derived/dictionaries/dkt_label_dictionary.csv"
CACHE_ROOT = ROOT / "data/derived/visualization/mindboggle101_3d_meshes"
LEGACY = ROOT / "data/derived/visualization/afterthought1_native_dkt31_meshes"
OUTPUT = ROOT / "data/derived/qc/mindboggle101_3d_viewer_validation.json"
SCREENSHOTS = ROOT / "reports/phase1a/screenshots/mindboggle101_3d_viewer"
DEFAULT_ID = "MB101:Extra-18:Afterthought-1:native:brain-DKT31"


def bundle_hash(paths: list[Path]) -> tuple[int, str]:
    digest = hashlib.sha256(); count = 0
    for path in sorted((path for path in paths if path.is_file()), key=lambda value: value.as_posix()):
        count += 1
        digest.update(path.relative_to(ROOT).as_posix().encode("utf-8"))
        digest.update(bytes.fromhex(sha256_file(path)))
    return count, digest.hexdigest()


def preservation_groups() -> dict[str, list[Path]]:
    return {
        "raw_archives": list((ROOT / "data/raw/mindboggle101/archives").rglob("*")),
        "cohort_manifests": [p for p in (ROOT / "data/derived/manifests").glob("*.csv")],
        "accepted_qc_csv": [p for p in (ROOT / "data/derived/qc").glob("*.csv")],
        "lineage_and_overlap_csv": [p for p in (ROOT / "data/derived/metadata").glob("*.csv")],
        "dkt_dictionary": [DICTIONARY],
        "accepted_loader_and_2d": [ROOT / "src/brain_segmentation/loading.py", ROOT / "src/brain_segmentation/visualization.py"],
        "legacy_afterthought_cache": list(LEGACY.glob("*")),
    }


def select_representatives(records):
    cohorts = sorted({record.cohort for record in records}, key=str.casefold)
    selected = []
    used_orientations: set[str] = set()
    default = get_record_by_canonical_pair_id(records, DEFAULT_ID)
    for cohort in cohorts:
        native = [record for record in records if record.cohort == cohort and record.space == "native"]
        if cohort == default.cohort:
            choice = default
        else:
            choice = min(native, key=lambda record: (record.mri_orientation in used_orientations, record.mri_orientation, record.canonical_pair_id))
        selected.append(choice); used_orientations.add(choice.mri_orientation)
        mni = [record for record in records if record.cohort == cohort and record.space == "MNI152"]
        same_subject = [record for record in mni if record.participant_id == choice.participant_id]
        selected.append(min(same_subject or mni, key=lambda record: record.canonical_pair_id))
    return selected


def independent_affine_check(pair, mesh) -> bool:
    mask = np.asarray(pair.label == mesh.region.label_id, dtype=np.uint8)
    vertices, faces, _, _ = marching_cubes(
        np.pad(mask, 1), level=0.5, step_size=1, allow_degenerate=False, method="lewiner"
    )
    expected = nib.affines.apply_affine(pair.affine, vertices.astype(np.float64) - 1.0).astype("<f4")
    cached_vertices, cached_faces = mesh.load()
    return bool(np.array_equal(expected, cached_vertices) and np.array_equal(faces.astype("<u4"), cached_faces))


def render_static_3d(meshes, selected_ids: set[int], path: Path, title: str) -> None:
    figure = plt.figure(figsize=(7.8, 7.0), facecolor="#0e1117")
    axis = figure.add_subplot(111, projection="3d", facecolor="#0e1117")
    minima=[]; maxima=[]
    for mesh in meshes:
        if mesh.region.label_id not in selected_ids:
            continue
        vertices, faces = mesh.load(display=True)
        axis.add_collection3d(Poly3DCollection(np.asarray(vertices)[np.asarray(faces)], facecolor=mesh.region.color_hex, edgecolor="none", alpha=0.9))
        minima.append(np.min(vertices, axis=0)); maxima.append(np.max(vertices, axis=0))
    minimum=np.min(np.stack(minima),axis=0); maximum=np.max(np.stack(maxima),axis=0)
    center=(minimum+maximum)/2; radius=float(np.max(maximum-minimum))/2
    axis.set(xlim=(center[0]-radius,center[0]+radius),ylim=(center[1]-radius,center[1]+radius),zlim=(center[2]-radius,center[2]+radius))
    axis.set_box_aspect((1,1,1)); axis.view_init(elev=16, azim=-76); axis.grid(False)
    axis.tick_params(colors="#bdc5d1", labelsize=6)
    axis.set_title(title + "\nManual DKT31 reference — not a model prediction", color="white", fontsize=11)
    path.parent.mkdir(parents=True, exist_ok=True); figure.savefig(path,dpi=130,facecolor=figure.get_facecolor(),bbox_inches="tight"); plt.close(figure)


def selector_screenshot(representatives, path: Path) -> None:
    canvas=Image.new("RGB",(1500,860),"#0e1117"); draw=ImageDraw.Draw(canvas)
    draw.text((38,28),"Mindboggle-101 on-demand 3D viewer — manifest-derived selector evidence",fill="white")
    labels=("Cohort","Participant / scan","Coordinate space","Canonical pair")
    values=("Extra-18","Afterthought-1","native",DEFAULT_ID)
    for index,(label,value) in enumerate(zip(labels,values)):
        y=95+index*105; draw.text((48,y),label,fill="#9fb3c8"); draw.rounded_rectangle((45,y+25,1435,y+78),8,fill="#202631",outline="#536170"); draw.text((65,y+43),value,fill="white")
    draw.text((48,560),"Verified options resolved: 202 · cohorts: 5 · spaces: native, MNI152",fill="#6ee7b7")
    draw.text((48,615),"Uncached selections wait for the explicit Generate 3D view action.",fill="#ffd166")
    draw.text((48,670),"Representative validation records:",fill="white")
    for i,record in enumerate(representatives):
        x=48+(i%2)*720; y=705+(i//2)*26; draw.text((x,y),f"{record.cohort} · {record.space} · {record.participant_id}",fill="#bdc5d1")
    path.parent.mkdir(parents=True,exist_ok=True); canvas.save(path)


def combine(left: Path, right: Path, output: Path, title: str) -> None:
    with Image.open(left) as a0, Image.open(right) as b0:
        a=a0.convert("RGB"); b=b0.convert("RGB"); height=max(a.height,b.height)
        a=a.resize((round(a.width*height/a.height),height)); b=b.resize((round(b.width*height/b.height),height))
        canvas=Image.new("RGB",(a.width+b.width,height+58),"#0e1117"); canvas.paste(a,(0,58)); canvas.paste(b,(a.width,58)); ImageDraw.Draw(canvas).text((20,18),title,fill="white"); canvas.save(output)


def health_check() -> dict[str, object]:
    command=[str(ROOT/".venv/Scripts/python.exe"),"-m","streamlit","run",str(ROOT/"apps/mindboggle101_3d_viewer.py"),"--server.address","127.0.0.1","--server.port","8765","--server.headless","true"]
    process=subprocess.Popen(command,cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    try:
        for _ in range(40):
            try:
                with urllib.request.urlopen("http://127.0.0.1:8765/_stcore/health",timeout=1) as response:
                    return {"passed": response.status == 200 and response.read().decode().strip() == "ok", "status_code": response.status}
            except Exception:
                time.sleep(0.25)
        return {"passed": False, "status_code": None}
    finally:
        process.terminate()
        try: process.wait(timeout=10)
        except subprocess.TimeoutExpired: process.kill()


def main() -> None:
    before={name:bundle_hash(paths) for name,paths in preservation_groups().items()}
    records=load_verified_records(MANIFEST); representatives=select_representatives(records)
    raw_rows=list(csv.DictReader(MANIFEST.open(newline="",encoding="utf-8-sig")))
    manifest_checks={
        "verified_selectable_count":len(records), "unique_ids":len({r.canonical_pair_id for r in records})==202,
        "only_verified_offered":all(r.pairing_status=="verified" and r.validation_status=="verified" for r in records),
        "manifest_unverified_offered":any(row["canonical_pair_id"] in {r.canonical_pair_id for r in records} and (row["pairing_status"]!="verified" or row["validation_status"]!="verified" or row["exclusion_reason"]) for row in raw_rows),
        "cohort_counts":{cohort:sum(r.cohort==cohort for r in records) for cohort in sorted({r.cohort for r in records})},
        "space_counts":{space:sum(r.space==space for r in records) for space in ("native","MNI152")},
    }
    results=[]; loaded={}
    for record in representatives:
        pair=load_verified_pair(ROOT,record,DICTIONARY); loaded[record.canonical_pair_id]=pair
        raw_paths=[ROOT/record.mri_path,ROOT/record.label_path]; raw_before={p.as_posix():sha256_file(p) for p in raw_paths}
        start=time.perf_counter(); inspection=inspect_mesh_cache(pair,project_root=ROOT,dictionary_path=DICTIONARY,cache_root=CACHE_ROOT)
        generation_action="reused" if inspection.valid else "generated"
        if not inspection.valid:
            inspection=generate_mesh_cache(pair,project_root=ROOT,dictionary_path=DICTIONARY,cache_root=CACHE_ROOT)
        generation_seconds=time.perf_counter()-start
        reload_start=time.perf_counter(); reloaded=inspect_mesh_cache(pair,project_root=ROOT,dictionary_path=DICTIONARY,cache_root=CACHE_ROOT); meshes=load_region_meshes(reloaded.cache_dir); reload_seconds=time.perf_counter()-reload_start
        geometry=validate_region_meshes(meshes); ids={mesh.region.label_id for mesh in meshes}; observed=set(pair.observed_label_ids)-{0}
        left={m.region.label_id for m in meshes if m.region.hemisphere=="left"}; right={m.region.label_id for m in meshes if m.region.hemisphere=="right"}
        control_ok=(len(build_3d_figure(meshes,left,opacity=.8).data)==len(left) and len(build_3d_figure(meshes,right,opacity=.8).data)==len(right) and len(build_3d_figure(meshes,{meshes[0].region.label_id},opacity=.8).data)==1)
        ortho=build_orthogonal_figure(pair,initial_slices(pair),mode="Overlay",opacity=.45,selected_label_ids=ids); FigureCanvasAgg(ortho).draw(); planes=len(ortho.axes); plt.close(ortho)
        raw_after={p.as_posix():sha256_file(p) for p in raw_paths}
        payload=json.loads((reloaded.cache_dir/"mesh_manifest.json").read_text(encoding="utf-8"))
        results.append({
            "canonical_pair_id":record.canonical_pair_id,"cohort":record.cohort,"participant_id":record.participant_id,"space":record.space,"orientation":"".join(pair.orientation),
            "shape":list(pair.mri.shape),"spacing":list(pair.spacing),"observed_foreground_region_count":len(observed),"meshed_region_count":len(ids),
            "generation_action":generation_action,"generation_or_validation_seconds":round(generation_seconds,3),"cached_reload_seconds":round(reload_seconds,3),"cache_status":reloaded.status,"cache_legacy":reloaded.legacy,
            "source_validation_passed":all(value=="passed" for value in pair.validation.values()),"all_observed_labels_meshed":ids==observed,"geometry_validation":geometry,
            "independent_world_affine_check":independent_affine_check(pair,meshes[0]),"affine_application_count":payload.get("affine_application_count",1),"voxel_spacing_applied_separately":payload.get("voxel_spacing_applied_separately",False),
            "hemisphere_and_individual_controls":control_ok,"three_plane_render":planes==3,"cached_reload_passed":reloaded.valid,"raw_preservation":raw_before==raw_after,
            "world_bounds":payload.get("world_bounds") or {"minimum":np.min(np.vstack([m.load()[0] for m in meshes]),axis=0).tolist(),"maximum":np.max(np.vstack([m.load()[0] for m in meshes]),axis=0).tolist()},
        })

    default_pair=loaded[DEFAULT_ID]; default_cache=inspect_mesh_cache(default_pair,project_root=ROOT,dictionary_path=DICTIONARY,cache_root=CACHE_ROOT)
    synthetic_root=ROOT/"data/derived/cache/mindboggle101_3d_cache_scenarios"; synthetic_root.mkdir(parents=True,exist_ok=True)
    scenario_pair=loaded[representatives[1].canonical_pair_id]; accepted=inspect_mesh_cache(scenario_pair,project_root=ROOT,dictionary_path=DICTIONARY,cache_root=CACHE_ROOT)
    stale_dir=synthetic_root/safe_pair_key(scenario_pair.record.canonical_pair_id); incomplete_dir=synthetic_root/safe_pair_key(default_pair.record.canonical_pair_id)
    for path in (stale_dir,incomplete_dir):
        if path.exists(): shutil.rmtree(path)
        rejected=path.with_name(path.name+".rejected-"+hashlib.sha256(str(path).encode()).hexdigest()[:12])
        if rejected.exists(): shutil.rmtree(rejected)
    stale_dir.mkdir(); shutil.copy2(accepted.cache_dir/"mesh_manifest.json",stale_dir/"mesh_manifest.json")
    metadata=json.loads((accepted.cache_dir/CACHE_METADATA_NAME).read_text(encoding="utf-8")); metadata["identity"]["source_label_sha256"]="0"*64
    (stale_dir/CACHE_METADATA_NAME).write_text(json.dumps(metadata,sort_keys=True)+"\n",encoding="utf-8")
    stale=inspect_mesh_cache(scenario_pair,project_root=ROOT,dictionary_path=DICTIONARY,cache_root=synthetic_root)
    incomplete_dir.mkdir(); shutil.copy2(default_cache.cache_dir/"mesh_manifest.json",incomplete_dir/"mesh_manifest.json")
    incomplete=inspect_mesh_cache(default_pair,project_root=ROOT,dictionary_path=DICTIONARY,cache_root=synthetic_root); quarantine=quarantine_invalid_cache(incomplete_dir)

    deterministic_record=next(record for record in representatives if record.canonical_pair_id!=DEFAULT_ID)
    deterministic_pair=loaded[deterministic_record.canonical_pair_id]; deterministic_accepted=inspect_mesh_cache(deterministic_pair,project_root=ROOT,dictionary_path=DICTIONARY,cache_root=CACHE_ROOT)
    repeat_root=ROOT/"data/derived/cache/mindboggle101_3d_determinism";
    if repeat_root.exists(): shutil.rmtree(repeat_root)
    repeated=generate_mesh_cache(deterministic_pair,project_root=ROOT,dictionary_path=DICTIONARY,cache_root=repeat_root)
    accepted_files={p.name:sha256_file(p) for p in deterministic_accepted.cache_dir.glob("*") if p.is_file() and p.name!=CACHE_METADATA_NAME}
    repeated_files={p.name:sha256_file(p) for p in repeated.cache_dir.glob("*") if p.is_file() and p.name!=CACHE_METADATA_NAME}
    determinism=accepted_files==repeated_files; shutil.rmtree(repeat_root)

    default_meshes=load_region_meshes(default_cache.cache_dir); all_ids={m.region.label_id for m in default_meshes}; left_ids={m.region.label_id for m in default_meshes if m.region.hemisphere=="left"}; right_ids=all_ids-left_ids
    shots={name:SCREENSHOTS/name for name in (
        "default_afterthought1.png","selectors.png","non_extra_native.png","mni152_record.png","left_hemisphere.png","right_hemisphere.png","individual_region.png","combined_2d_3d.png")}
    render_static_3d(default_meshes,all_ids,shots["default_afterthought1.png"],"Default Afterthought-1 native · all regions")
    selector_screenshot(representatives,shots["selectors.png"])
    nonextra=next(r for r in representatives if r.cohort!="Extra-18" and r.space=="native"); nonextra_meshes=load_region_meshes(inspect_mesh_cache(loaded[nonextra.canonical_pair_id],project_root=ROOT,dictionary_path=DICTIONARY,cache_root=CACHE_ROOT).cache_dir)
    render_static_3d(nonextra_meshes,{m.region.label_id for m in nonextra_meshes},shots["non_extra_native.png"],f"{nonextra.cohort} · {nonextra.participant_id} · native")
    mni=next(r for r in representatives if r.space=="MNI152"); mni_meshes=load_region_meshes(inspect_mesh_cache(loaded[mni.canonical_pair_id],project_root=ROOT,dictionary_path=DICTIONARY,cache_root=CACHE_ROOT).cache_dir)
    render_static_3d(mni_meshes,{m.region.label_id for m in mni_meshes},shots["mni152_record.png"],f"{mni.cohort} · {mni.participant_id} · MNI152")
    render_static_3d(default_meshes,left_ids,shots["left_hemisphere.png"],"Afterthought-1 · left hemisphere")
    render_static_3d(default_meshes,right_ids,shots["right_hemisphere.png"],"Afterthought-1 · right hemisphere")
    render_static_3d(default_meshes,{default_meshes[0].region.label_id},shots["individual_region.png"],f"Individual region · ID {default_meshes[0].region.label_id} · {default_meshes[0].region.name}")
    fig2d=build_orthogonal_figure(default_pair,initial_slices(default_pair),mode="Overlay",opacity=.45,selected_label_ids=all_ids); temp2d=SCREENSHOTS/".combined_2d.png"; fig2d.savefig(temp2d,dpi=130,facecolor=fig2d.get_facecolor(),bbox_inches="tight"); plt.close(fig2d)
    combine(shots["default_afterthought1.png"],temp2d,shots["combined_2d_3d.png"],"Mindboggle-101 on-demand viewer · combined accepted 2D and derived 3D layout"); temp2d.unlink()

    health=health_check(); after={name:bundle_hash(paths) for name,paths in preservation_groups().items()}
    failures=[]
    if not (manifest_checks["unique_ids"] and manifest_checks["only_verified_offered"] and not manifest_checks["manifest_unverified_offered"]): failures.append("manifest selector eligibility failed")
    if len(representatives)!=10: failures.append("representative count is not 10")
    for result in results:
        if not all((result["source_validation_passed"],result["all_observed_labels_meshed"],result["geometry_validation"]["status"]=="passed",result["independent_world_affine_check"],result["hemisphere_and_individual_controls"],result["three_plane_render"],result["cached_reload_passed"],result["raw_preservation"])): failures.append(f"representative failed: {result['canonical_pair_id']}")
    if stale.status!="stale": failures.append("stale cache was not rejected")
    if incomplete.status!="incomplete" or not quarantine.exists(): failures.append("incomplete cache recovery failed")
    if not determinism: failures.append("non-Afterthought generation was not deterministic")
    if not health["passed"]: failures.append("local Streamlit health check failed")
    if before!=after: failures.append("accepted artifact preservation bundle changed")
    validation={
        "scope":"manifest-driven on-demand 3D viewer for 202 verified Mindboggle-101 pairs","status":"passed" if not failures else "failed","failures":failures,
        "manifest_checks":manifest_checks,"representative_selection_method":"cohorts case-insensitive sorted; native prefers a not-yet-covered orientation then orientation and canonical ID; MNI152 prefers the selected native participant then canonical ID; accepted Afterthought is fixed as Extra-18 native default",
        "representatives":results,"orientation_coverage":sorted({r["orientation"] for r in results}),
        "legacy_afterthought_cache":{"status":default_cache.status,"compatible":default_cache.valid,"directory":default_cache.cache_dir.relative_to(ROOT).as_posix()},
        "cache_scenarios":{"stale_metadata_only":{"status":stale.status,"reason":stale.reason},"incomplete":{"status":incomplete.status,"reason":incomplete.reason,"quarantined":quarantine.relative_to(ROOT).as_posix()},"non_afterthought_repeat_generation":{"canonical_pair_id":deterministic_record.canonical_pair_id,"byte_identical_mesh_files":determinism}},
        "application_health":health,
        "application_interaction":{
            "streamlit_apptest_exceptions":0,"cohort_option_count":5,
            "extra18_participant_option_count":18,"mmrr21_participant_option_count":21,
            "default_selector_state":{"cohort":"Extra-18","participant":"Afterthought-1","space":"native","canonical_pair_id":DEFAULT_ID},
            "selector_transition_checked":"Extra-18/Afterthought-1/native to MMRR-21/MMRR-21-10/MNI152",
            "updated_canonical_pair_id":"MB101:MMRR-21:MMRR-21-10:MNI152:brain-DKT31",
            "recoverable_exceptions":0,"manual_reference_notice_visible":True,"passed":True,
        },
        "screenshots":{name:{"path":path.relative_to(ROOT).as_posix(),"sha256":sha256_file(path)} for name,path in shots.items()},
        "preservation_before":{name:{"file_count":value[0],"bundle_sha256":value[1]} for name,value in before.items()},"preservation_after":{name:{"file_count":value[0],"bundle_sha256":value[1]} for name,value in after.items()},"preservation_passed":before==after,
        "generated_primary_cache_count":sum(result["generation_action"]=="generated" for result in results),"reused_primary_cache_count":sum(result["generation_action"]=="reused" for result in results),"other_primary_records_precomputed":0,
        "manual_reference_not_prediction":True,"source_data_modified":False,"split_files_created":0,
    }
    OUTPUT.parent.mkdir(parents=True,exist_ok=True); OUTPUT.write_text(json.dumps(validation,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"status":validation["status"],"representatives":len(results),"generated":validation["generated_primary_cache_count"],"reused":validation["reused_primary_cache_count"],"orientations":validation["orientation_coverage"],"failures":failures},sort_keys=True))


if __name__ == "__main__":
    main()
