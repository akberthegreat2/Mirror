"""Pytest bootstrap for the Mirror monorepo.

Pytest discovers this file before importing any package tests. We ensure every
workspace package's ``src`` directory is importable from the repository root.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
for src in sorted((ROOT / "packages").glob("*/src")):
    if src.is_dir():
        path = str(src)
        if path not in sys.path:
            sys.path.insert(0, path)
