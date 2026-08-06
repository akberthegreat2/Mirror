"""Public TOML helpers for Mirror configuration and CLI loading."""

from __future__ import annotations

from typing import Any, BinaryIO

try:
    import tomllib as _toml
except ModuleNotFoundError:  # pragma: no cover - Python < 3.11
    import tomli as _toml  # type: ignore[no-redef]


def load(fp: BinaryIO) -> dict[str, Any]:
    """Load TOML data from a binary file object."""
    return _toml.load(fp)


def loads(text: str) -> dict[str, Any]:
    """Load TOML data from a string."""
    return _toml.loads(text)
