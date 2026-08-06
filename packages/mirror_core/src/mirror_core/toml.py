"""TOML parsing compatibility layer."""

from __future__ import annotations

import sys
from typing import Any, BinaryIO

if sys.version_info >= (3, 11):
    import tomllib as tomli
else:
    import tomli  # type: ignore[import-not-found]


def loads(s: str) -> dict[str, Any]:
    return tomli.loads(s)  # type: ignore[no-any-return]


def load(f: BinaryIO) -> dict[str, Any]:
    return tomli.load(f)  # type: ignore[no-any-return]
