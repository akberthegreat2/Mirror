"""Repository-local interpreter bootstrap for the Mirror monorepo.

When running from a source checkout, add every package's ``src`` directory to
``sys.path`` so package tests and ad hoc scripts can import the workspace
packages without requiring editable installs first.
"""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
_PACKAGES = _ROOT / "packages"

if _PACKAGES.is_dir():
    for src in sorted(_PACKAGES.glob("*/src")):
        if src.is_dir():
            path = str(src)
            if path not in sys.path:
                sys.path.insert(0, path)
