"""Local entry point for the manifest-driven Mindboggle-101 3D viewer."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / "data/derived/cache/matplotlib"))
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from brain_segmentation.streamlit_3d_viewer import run_app  # noqa: E402

run_app(ROOT)

