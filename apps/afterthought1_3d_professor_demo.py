"""Compatible redirect to the shared Mindboggle-101 viewer implementation."""

from __future__ import annotations

import runpy
from pathlib import Path


runpy.run_path(str(Path(__file__).with_name("mindboggle101_3d_viewer.py")), run_name="__main__")

