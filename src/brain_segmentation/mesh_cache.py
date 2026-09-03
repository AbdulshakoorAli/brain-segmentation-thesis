"""Versioned, provenance-bound, atomic caches for manual-DKT31 meshes."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import numpy as np

from brain_segmentation.loading import LoadedCanonicalPair
from brain_segmentation.mesh_visualization import (
    DISPLAY_MESH_ALGORITHM,
    MESH_ALGORITHM,
    build_region_meshes,
    load_region_meshes,
    sha256_file,
    validate_region_meshes,
)


CACHE_SCHEMA_VERSION = 2
CACHE_CODE_VERSION = "mindboggle101-3d-cache-1"
CACHE_METADATA_NAME = "cache_metadata.json"
LEGACY_AFTERTHOUGHT_DIR = "afterthought1_native_dkt31_meshes"
FULL_LEVEL = {"name": "full-resolution scientific mesh", "step_size": 1}
DISPLAY_LEVEL = {"name": "reduced display mesh", "step_size": 2}


@dataclass(frozen=True)
class CacheInspection:
    status: str
    cache_dir: Path
    reason: str
    legacy: bool = False

    @property
    def valid(self) -> bool:
        return self.status == "valid"


def safe_pair_key(canonical_pair_id: str) -> str:
    """Return a deterministic directory key that never embeds manifest text."""
    return "pair-" + hashlib.sha256(canonical_pair_id.encode("utf-8")).hexdigest()[:24]


def _json_bytes(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _identity(
    pair: LoadedCanonicalPair,
    *,
    project_root: Path,
    dictionary_path: Path,
) -> dict[str, object]:
    label_path = project_root / pair.record.label_path
    return {
        "cache_schema_version": CACHE_SCHEMA_VERSION,
        "cache_code_version": CACHE_CODE_VERSION,
        "canonical_pair_id": pair.record.canonical_pair_id,
        "source_label_relative_path": pair.record.label_path.replace("\\", "/"),
        "source_label_sha256": sha256_file(label_path),
        "nifti_affine": np.asarray(pair.affine, dtype=np.float64).tolist(),
        "observed_label_ids": list(pair.observed_label_ids),
        "mesh_algorithm": MESH_ALGORITHM,
        "mesh_parameters": {
            "level": 0.5,
            "allow_degenerate": False,
            "method": "lewiner",
            "padded_binary_mask": True,
            "affine_application_count": 1,
            "voxel_spacing_applied_separately": False,
        },
        "full_resolution_level": FULL_LEVEL,
        "display_mesh_algorithm": DISPLAY_MESH_ALGORITHM,
        "display_mesh_level": DISPLAY_LEVEL,
        "dictionary_relative_path": str(dictionary_path.relative_to(project_root)).replace("\\", "/"),
        "dictionary_sha256": sha256_file(dictionary_path),
    }


def _legacy_dir_for_pair(
    cache_root: Path, pair: LoadedCanonicalPair
) -> Path | None:
    candidate = cache_root.parent / LEGACY_AFTERTHOUGHT_DIR
    manifest_path = candidate / "mesh_manifest.json"
    if not manifest_path.is_file():
        return None
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if payload.get("canonical_pair_id") == pair.record.canonical_pair_id:
        return candidate
    return None


def cache_dir_for_pair(cache_root: Path, pair: LoadedCanonicalPair) -> Path:
    legacy = _legacy_dir_for_pair(cache_root, pair)
    return legacy if legacy is not None else cache_root / safe_pair_key(pair.record.canonical_pair_id)


def _verify_mesh_files(cache_dir: Path, payload: dict[str, object]) -> list[str]:
    failures: list[str] = []
    rows = payload.get("regions")
    if not isinstance(rows, list) or not rows:
        return ["mesh manifest has no region rows"]
    for row in rows:
        if not isinstance(row, dict):
            failures.append("invalid mesh row")
            continue
        for prefix in ("", "display_"):
            for kind in ("vertices", "faces"):
                filename = row.get(f"{prefix}{kind}_file")
                expected_hash = row.get(f"{prefix}{kind}_sha256")
                if not isinstance(filename, str) or Path(filename).name != filename:
                    failures.append(f"unsafe or missing mesh filename for label {row.get('label_id')}")
                    continue
                path = cache_dir / filename
                if not path.is_file():
                    failures.append(f"missing mesh file {filename}")
                elif expected_hash and sha256_file(path) != expected_hash:
                    failures.append(f"mesh hash mismatch {filename}")
    return failures


def inspect_mesh_cache(
    pair: LoadedCanonicalPair,
    *,
    project_root: Path,
    dictionary_path: Path,
    cache_root: Path,
) -> CacheInspection:
    cache_dir = cache_dir_for_pair(cache_root, pair)
    manifest_path = cache_dir / "mesh_manifest.json"
    if not cache_dir.exists():
        return CacheInspection("missing", cache_dir, "no derived cache exists")
    if not manifest_path.is_file():
        return CacheInspection("incomplete", cache_dir, "mesh_manifest.json is absent")
    try:
        mesh_payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return CacheInspection("incomplete", cache_dir, f"mesh manifest is unreadable: {exc}")

    expected = _identity(pair, project_root=project_root, dictionary_path=dictionary_path)
    metadata_path = cache_dir / CACHE_METADATA_NAME
    legacy = not metadata_path.is_file()
    if legacy:
        compatible = {
            "canonical_pair_id": mesh_payload.get("canonical_pair_id"),
            "source_label_relative_path": str(mesh_payload.get("label_path", "")).replace("\\", "/"),
            "source_label_sha256": mesh_payload.get("label_sha256"),
            "nifti_affine": mesh_payload.get("affine"),
            "observed_label_ids": [0] + [int(row["label_id"]) for row in mesh_payload.get("regions", [])],
            "mesh_algorithm": mesh_payload.get("algorithm"),
            "display_mesh_algorithm": mesh_payload.get("display_algorithm"),
            "dictionary_sha256": mesh_payload.get("dictionary_sha256"),
        }
        for key, actual in compatible.items():
            if actual != expected[key]:
                return CacheInspection("stale", cache_dir, f"legacy provenance mismatch: {key}", True)
    else:
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            return CacheInspection("incomplete", cache_dir, f"cache metadata is unreadable: {exc}")
        if metadata.get("identity") != expected:
            return CacheInspection("stale", cache_dir, "cache identity does not match selected source")
        if metadata.get("complete") is not True:
            return CacheInspection("incomplete", cache_dir, "cache completion marker is absent")
        if metadata.get("mesh_manifest_sha256") != sha256_file(manifest_path):
            return CacheInspection("stale", cache_dir, "mesh manifest hash does not match cache metadata")

    failures = _verify_mesh_files(cache_dir, mesh_payload)
    if failures:
        return CacheInspection("incomplete", cache_dir, "; ".join(failures[:3]), legacy)
    mesh_validation = validate_region_meshes(load_region_meshes(cache_dir))
    if mesh_validation["status"] != "passed":
        return CacheInspection("incomplete", cache_dir, "; ".join(mesh_validation["failures"][:3]), legacy)
    represented = {int(row["label_id"]) for row in mesh_payload["regions"]}
    expected_regions = set(pair.observed_label_ids) - {0}
    if represented != expected_regions:
        return CacheInspection("stale", cache_dir, "cached regions differ from observed source labels", legacy)
    return CacheInspection("valid", cache_dir, "cache provenance and geometry validated", legacy)


def quarantine_invalid_cache(cache_dir: Path) -> Path:
    """Move one known-invalid cache aside without deleting it."""
    marker = hashlib.sha256(str(cache_dir).encode("utf-8")).hexdigest()[:12]
    quarantine = cache_dir.with_name(cache_dir.name + f".rejected-{marker}")
    if quarantine.exists():
        raise FileExistsError(f"Invalid-cache quarantine already exists: {quarantine}")
    os.replace(cache_dir, quarantine)
    return quarantine


def generate_mesh_cache(
    pair: LoadedCanonicalPair,
    *,
    project_root: Path,
    dictionary_path: Path,
    cache_root: Path,
    progress_callback: Callable[[int, int, int], None] | None = None,
) -> CacheInspection:
    """Generate one cache in a temporary directory and publish it atomically."""
    prior = inspect_mesh_cache(
        pair,
        project_root=project_root,
        dictionary_path=dictionary_path,
        cache_root=cache_root,
    )
    if prior.valid:
        return prior
    target = cache_root / safe_pair_key(pair.record.canonical_pair_id)
    cache_root.mkdir(parents=True, exist_ok=True)
    temporary = cache_root / (target.name + f".building-{os.getpid()}")
    if temporary.exists():
        shutil.rmtree(temporary)
    temporary.mkdir(parents=False)
    try:
        payload = build_region_meshes(
            pair,
            project_root=project_root,
            dictionary_path=dictionary_path,
            output_dir=temporary,
            progress_callback=progress_callback,
        )
        identity = _identity(pair, project_root=project_root, dictionary_path=dictionary_path)
        metadata = {
            "complete": True,
            "identity": identity,
            "mesh_manifest_sha256": sha256_file(temporary / "mesh_manifest.json"),
            "region_count": len(payload["regions"]),
        }
        metadata_tmp = temporary / (CACHE_METADATA_NAME + ".tmp")
        metadata_tmp.write_bytes(_json_bytes(metadata))
        os.replace(metadata_tmp, temporary / CACHE_METADATA_NAME)
        temporary_meshes = load_region_meshes(temporary)
        validation = validate_region_meshes(temporary_meshes)
        if validation["status"] != "passed":
            raise ValueError(f"Generated cache failed geometry validation: {validation['failures']}")
        if target.exists():
            current = inspect_mesh_cache(
                pair,
                project_root=project_root,
                dictionary_path=dictionary_path,
                cache_root=cache_root,
            )
            if current.valid and current.cache_dir == target:
                shutil.rmtree(temporary)
                return current
            quarantine_invalid_cache(target)
        os.replace(temporary, target)
    except Exception:
        if temporary.exists():
            shutil.rmtree(temporary)
        raise
    return inspect_mesh_cache(
        pair,
        project_root=project_root,
        dictionary_path=dictionary_path,
        cache_root=cache_root,
    )
