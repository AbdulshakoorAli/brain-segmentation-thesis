"""Shared Streamlit UI for manifest-driven manual-DKT31 viewing."""

from __future__ import annotations

import hashlib
from pathlib import Path

import matplotlib.pyplot as plt
import streamlit as st

from brain_segmentation.loading import get_record_by_canonical_pair_id, load_verified_pair, load_verified_records
from brain_segmentation.mesh_cache import generate_mesh_cache, inspect_mesh_cache
from brain_segmentation.mesh_visualization import (
    PLOTLY_STREAMLIT_CONFIG, build_3d_figure, build_orthogonal_figure,
    initial_slices, load_region_meshes,
)
from brain_segmentation.visualization import planes_for_orientation


DEFAULT_PAIR_ID = "MB101:Extra-18:Afterthought-1:native:brain-DKT31"
NOTICE = "Manual DKT31 reference segmentation — not a model prediction."


def _key(pair_id: str, suffix: str) -> str:
    return f"{suffix}_{hashlib.sha256(pair_id.encode()).hexdigest()[:10]}"


def run_app(project_root: Path) -> None:
    manifest = project_root / "data/derived/manifests/mindboggle101_scan_manifest.csv"
    dictionary = project_root / "data/derived/dictionaries/dkt_label_dictionary.csv"
    cache_root = project_root / "data/derived/visualization/mindboggle101_3d_meshes"
    st.set_page_config(page_title="Mindboggle-101 manual DKT31 · 3D viewer", page_icon="🧠", layout="wide")
    st.title("Mindboggle-101 · manifest-driven 2D/3D manual-DKT31 viewer")
    st.warning(f"{NOTICE} This local research demonstration makes no medical or clinical claim.")

    try:
        records = load_verified_records(manifest)
        if len(records) != 202:
            raise ValueError(f"Expected 202 verified canonical records; found {len(records)}")
        default = get_record_by_canonical_pair_id(records, DEFAULT_PAIR_ID)
        cohorts = sorted({record.cohort for record in records}, key=str.casefold)
        cohort = st.sidebar.selectbox("Cohort", cohorts, index=cohorts.index(default.cohort))
        cohort_rows = [record for record in records if record.cohort == cohort]
        participant_options = sorted({record.participant_id for record in cohort_rows}, key=str.casefold)
        participant_default = default.participant_id if cohort == default.cohort else participant_options[0]
        participant = st.sidebar.selectbox(
            "Participant / scan", participant_options, index=participant_options.index(participant_default), key=f"participant_{cohort}"
        )
        participant_rows = [record for record in cohort_rows if record.participant_id == participant]
        spaces = [space for space in ("native", "MNI152") if any(row.space == space for row in participant_rows)]
        space_default = default.space if participant == default.participant_id and cohort == default.cohort else spaces[0]
        space = st.sidebar.selectbox(
            "Coordinate space", spaces, index=spaces.index(space_default), key=f"space_{cohort}_{participant}"
        )
        pair_ids = sorted(row.canonical_pair_id for row in participant_rows if row.space == space)
        pair_id = st.sidebar.selectbox("Canonical pair", pair_ids, key=f"pair_{cohort}_{participant}_{space}")
        record = get_record_by_canonical_pair_id(records, pair_id)
        pair = load_verified_pair(project_root, record, dictionary)
        cache = inspect_mesh_cache(
            pair, project_root=project_root, dictionary_path=dictionary, cache_root=cache_root
        )
    except Exception as exc:
        st.error(f"The selected verified record could not be resolved: {type(exc).__name__}: {exc}")
        return

    st.caption(
        f"{record.canonical_pair_id} · {record.participant_id} · {record.cohort} · {record.space} · "
        f"orientation {''.join(pair.orientation)} · shape {'×'.join(map(str, pair.mri.shape))} · "
        f"spacing {', '.join(f'{value:.6g}' for value in pair.spacing)} mm · "
        f"participant group {record.participant_group_id or 'unresolved'} · mesh cache {cache.status}"
    )
    if not cache.valid:
        st.info(
            f"3D cache status: {cache.status} ({cache.reason}). The source pair passed validation; "
            "no surface is generated until explicitly requested."
        )
        if st.button("Generate 3D view", type="primary"):
            progress = st.progress(0.0, text="Preparing deterministic DKT surfaces…")
            def update(done: int, total: int, label_id: int) -> None:
                progress.progress(done / total, text=f"Region {done}/{total} · DKT ID {label_id}")
            try:
                with st.status("Generating full-resolution and display meshes…") as status:
                    cache = generate_mesh_cache(
                        pair, project_root=project_root, dictionary_path=dictionary,
                        cache_root=cache_root, progress_callback=update,
                    )
                    if not cache.valid:
                        raise ValueError(cache.reason)
                    status.update(label="Mesh cache generated and validated", state="complete")
                st.rerun()
            except Exception as exc:
                st.error(f"3D generation failed safely: {type(exc).__name__}: {exc}")

    meshes = load_region_meshes(cache.cache_dir) if cache.valid else tuple()
    with st.sidebar:
        st.divider(); st.header("3D region controls")
        search = st.text_input("Region-name search", key=_key(pair_id, "search")).strip().casefold()
        left = st.checkbox("Left hemisphere", True, key=_key(pair_id, "left"))
        right = st.checkbox("Right hemisphere", True, key=_key(pair_id, "right"))
        hemispheres = {name for name, enabled in (("left", left), ("right", right)) if enabled}
        available = [mesh for mesh in meshes if mesh.region.hemisphere in hemispheres and (
            not search or search in mesh.region.name.casefold() or search == str(mesh.region.label_id)
        )]
        options = {f"{mesh.region.label_id} — {mesh.region.hemisphere} {mesh.region.name}": mesh.region.label_id for mesh in available}
        selected_key = _key(pair_id, "regions")
        if selected_key not in st.session_state:
            st.session_state[selected_key] = list(options)
        else:
            st.session_state[selected_key] = [value for value in st.session_state[selected_key] if value in options]
        col_all, col_none = st.columns(2)
        if col_all.button("Show all", use_container_width=True, key=_key(pair_id, "show_all")):
            st.session_state[selected_key] = list(options); st.rerun()
        if col_none.button("Hide all", use_container_width=True, key=_key(pair_id, "hide_all")):
            st.session_state[selected_key] = []; st.rerun()
        selected = st.multiselect("Individual regions", list(options), key=selected_key)
        selected_ids = {options[value] for value in selected}
        surface_opacity = st.slider("3D surface opacity", 0.10, 1.00, 0.82, 0.05, key=_key(pair_id, "surface_opacity"))
        if st.button("Reset 3D camera", key=_key(pair_id, "reset_camera")):
            camera_key = _key(pair_id, "camera_revision")
            st.session_state[camera_key] = st.session_state.get(camera_key, 0) + 1
        st.divider(); st.header("2D controls")
        mode = st.radio("Display mode", ("Overlay", "MRI only", "Label only"), horizontal=True, key=_key(pair_id, "mode"))
        overlay_opacity = st.slider("2D overlay opacity", 0.0, 1.0, 0.45, 0.05, key=_key(pair_id, "overlay_opacity"))
        center = initial_slices(pair); chosen = list(center)
        for plane in planes_for_orientation(pair.orientation):
            chosen[plane.slice_axis] = st.slider(
                f"{plane.name} slice", 0, pair.mri.shape[plane.slice_axis] - 1,
                center[plane.slice_axis], key=_key(pair_id, f"{plane.name}_slice"),
            )

    pane_3d, pane_2d = st.columns([1.2, 1.0], gap="large")
    with pane_3d:
        st.subheader("Interactive 3D manual reference")
        st.caption("Drag to rotate · scroll to zoom · modebar supports pan/reset · hover for DKT metadata")
        if cache.valid:
            camera_key = _key(pair_id, "camera_revision")
            figure = build_3d_figure(
                meshes, selected_ids, opacity=surface_opacity,
                uirevision=f"{pair_id}:{st.session_state.get(camera_key, 0)}",
            )
            st.plotly_chart(figure, width="stretch", theme=None, config=PLOTLY_STREAMLIT_CONFIG)
        else:
            st.info("Press ‘Generate 3D view’ to create this record’s derived surfaces on demand.")
    with pane_2d:
        st.subheader("Accepted MRI/manual-label views")
        figure_2d = build_orthogonal_figure(
            pair, tuple(chosen), mode=mode, opacity=overlay_opacity,
            selected_label_ids=selected_ids if cache.valid else None,
        )
        st.pyplot(figure_2d, width="stretch"); plt.close(figure_2d)

    st.subheader("Selected DKT reference regions")
    st.dataframe([{
        "color": mesh.region.color_hex, "original_DKT_ID": mesh.region.label_id,
        "hemisphere": mesh.region.hemisphere, "region_name": mesh.region.name,
        "full_vertices": mesh.vertex_count, "full_faces": mesh.face_count,
        "display_vertices": mesh.display_vertex_count, "display_faces": mesh.display_face_count,
    } for mesh in meshes if mesh.region.label_id in selected_ids], width="stretch", hide_index=True)
    with st.expander("Scientific, cache, and provenance notes"):
        st.markdown(
            f"- {NOTICE}\n- Each selection uses the accepted read-only loader.\n"
            "- Full-resolution step-1 geometry remains separate from reduced step-2 display geometry.\n"
            "- The NIfTI affine is applied exactly once; voxel spacing is not applied separately.\n"
            "- Raw files are not rewritten; no resampling, normalization, reorientation, smoothing, or remapping occurs.\n"
            "- Uncached records generate only after the user presses Generate 3D view.\n"
            "- Licensing/provenance reconciliation remains unresolved; the application is local only."
        )

