"""Focused headless UI and launcher checks for the professor demo."""

from __future__ import annotations

import json
import os
import subprocess
import time
import urllib.request
from pathlib import Path

from streamlit.testing.v1 import AppTest


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "apps/afterthought1_3d_professor_demo.py"
VALIDATION = ROOT / "data/derived/qc/afterthought1_3d_demo_validation.json"
LAUNCHER = ROOT / "launch_afterthought1_3d_demo.cmd"


def exception_messages(app: AppTest) -> list[str]:
    return [str(item.message) for item in app.exception]


def run_app_test() -> dict[str, object]:
    app = AppTest.from_file(APP, default_timeout=180).run(timeout=180)
    initial_exceptions = exception_messages(app)
    initial = {
        "exceptions": initial_exceptions,
        "left_enabled": app.checkbox(key="left_hemisphere").value,
        "right_enabled": app.checkbox(key="right_hemisphere").value,
        "region_option_count": len(app.multiselect(key="selected_regions").options),
        "selected_region_count": len(app.multiselect(key="selected_regions").value),
        "manual_reference_notice_visible": any(
            "manual reference segmentation, not a model prediction" in item.value.lower()
            for item in app.warning
        ),
        "slice_values": {
            "axial": app.slider(key="axial_slice").value,
            "coronal": app.slider(key="coronal_slice").value,
            "sagittal": app.slider(key="sagittal_slice").value,
        },
    }

    app.checkbox(key="left_hemisphere").uncheck().run(timeout=180)
    right_only = {
        "exceptions": exception_messages(app),
        "region_option_count": len(app.multiselect(key="selected_regions").options),
        "selected_region_count": len(app.multiselect(key="selected_regions").value),
    }

    app.checkbox(key="left_hemisphere").check()
    app.checkbox(key="right_hemisphere").uncheck()
    app.run(timeout=180)
    left_only = {
        "exceptions": exception_messages(app),
        "region_option_count": len(app.multiselect(key="selected_regions").options),
        "selected_region_count": len(app.multiselect(key="selected_regions").value),
    }

    first_region = app.multiselect(key="selected_regions").options[0]
    app.multiselect(key="selected_regions").set_value([first_region])
    app.slider(key="surface_opacity").set_value(0.40)
    app.slider(key="overlay_opacity").set_value(0.30)
    for key in ("axial_slice", "coronal_slice", "sagittal_slice"):
        slider = app.slider(key=key)
        slider.set_value(slider.value + 1)
    app.radio(key="display_mode").set_value("Label only")
    app.run(timeout=180)
    adjusted = {
        "exceptions": exception_messages(app),
        "selected_regions": list(app.multiselect(key="selected_regions").value),
        "surface_opacity": app.slider(key="surface_opacity").value,
        "overlay_opacity": app.slider(key="overlay_opacity").value,
        "display_mode": app.radio(key="display_mode").value,
        "slice_values": {
            "axial": app.slider(key="axial_slice").value,
            "coronal": app.slider(key="coronal_slice").value,
            "sagittal": app.slider(key="sagittal_slice").value,
        },
    }

    passed = (
        not initial_exceptions
        and initial["left_enabled"]
        and initial["right_enabled"]
        and initial["region_option_count"] == 62
        and initial["selected_region_count"] == 62
        and initial["manual_reference_notice_visible"]
        and not right_only["exceptions"]
        and right_only["region_option_count"] == 31
        and not left_only["exceptions"]
        and left_only["region_option_count"] == 31
        and left_only["selected_region_count"] == 31
        and not adjusted["exceptions"]
        and len(adjusted["selected_regions"]) == 1
        and adjusted["surface_opacity"] == 0.40
        and adjusted["overlay_opacity"] == 0.30
        and adjusted["display_mode"] == "Label only"
    )
    return {
        "status": "passed" if passed else "failed",
        "initial": initial,
        "right_only": right_only,
        "left_only": left_only,
        "adjusted_controls": adjusted,
    }


def validate_launcher() -> dict[str, object]:
    environment = os.environ.copy()
    environment["BRAIN_DEMO_VALIDATE_ONLY"] = "1"
    result = subprocess.run(
        ["cmd.exe", "/d", "/c", str(LAUNCHER)],
        cwd=ROOT,
        env=environment,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    return {
        "status": "passed" if result.returncode == 0 and "LAUNCHER_VALIDATION_PASSED" in result.stdout else "failed",
        "return_code": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
        "one_click_path": str(LAUNCHER.relative_to(ROOT)).replace("\\", "/"),
        "launch_command": ".\\launch_afterthought1_3d_demo.cmd",
    }


def validate_local_server() -> dict[str, object]:
    port = 8765
    command = [
        str(ROOT / ".venv/Scripts/python.exe"),
        "-m",
        "streamlit",
        "run",
        str(APP),
        "--server.headless",
        "true",
        "--server.port",
        str(port),
        "--browser.gatherUsageStats",
        "false",
    ]
    creationflags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    process = subprocess.Popen(
        command,
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=creationflags,
    )
    healthy = False
    response_text = ""
    try:
        for _ in range(30):
            if process.poll() is not None:
                break
            try:
                with urllib.request.urlopen(
                    f"http://127.0.0.1:{port}/_stcore/health", timeout=2
                ) as response:
                    response_text = response.read().decode("utf-8", errors="replace")
                    healthy = response.status == 200 and response_text.strip() == "ok"
                if healthy:
                    break
            except OSError:
                time.sleep(1)
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=10)
    return {
        "status": "passed" if healthy else "failed",
        "health_url": f"http://127.0.0.1:{port}/_stcore/health",
        "response": response_text.strip(),
        "process_exit_after_validation": process.returncode,
    }


def main() -> None:
    payload = json.loads(VALIDATION.read_text(encoding="utf-8"))
    payload["streamlit_app_test"] = run_app_test()
    payload["windows_launcher"] = validate_launcher()
    payload["local_server_validation"] = validate_local_server()
    split_files = [path for path in (ROOT / "splits").rglob("*") if path.is_file()]
    mesh_roots = [
        path.name
        for path in (ROOT / "data/derived/visualization").iterdir()
        if path.is_dir()
    ]
    payload["split_files_created"] = len(split_files)
    payload["mesh_record_directories"] = sorted(mesh_roots)
    payload["other_record_meshes_created"] = len(
        [name for name in mesh_roots if name != "afterthought1_native_dkt31_meshes"]
    )
    failures = list(payload.get("failures", []))
    if payload["streamlit_app_test"]["status"] != "passed":
        failures.append("Streamlit app test failed")
    if payload["windows_launcher"]["status"] != "passed":
        failures.append("Windows launcher validation failed")
    if payload["local_server_validation"]["status"] != "passed":
        failures.append("local Streamlit server validation failed")
    if split_files:
        failures.append("split files exist")
    if payload["other_record_meshes_created"]:
        failures.append("mesh output exists for another record")
    payload["failures"] = failures
    payload["status"] = "passed" if not failures else "failed"
    VALIDATION.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": payload["status"],
        "streamlit_app_test": payload["streamlit_app_test"]["status"],
        "windows_launcher": payload["windows_launcher"]["status"],
        "local_server": payload["local_server_validation"]["status"],
        "split_files": len(split_files),
        "other_record_meshes": payload["other_record_meshes_created"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
