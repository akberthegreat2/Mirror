"""TOML parsing compatibility layer."""

from __future__ import annotations

import sys
from typing import Any, BinaryIO

if sys.version_info >= (3, 11):
    import tomllib as tomli
else:
    import tomli


def loads(s: str) -> dict[str, Any]:
    return dict(tomli.loads(s))


def load(f: BinaryIO) -> dict[str, Any]:
    return dict(tomli.load(f))
