"""TOML loading compatibility shim.

Every package in this workspace declares ``requires-python = ">=3.10"``, but
the standard library only gained ``tomllib`` in Python 3.11. Code that does a
bare ``import tomllib`` therefore breaks on 3.10 despite that being a
supported, advertised version.

Anything in Mirror that needs to parse TOML should import ``load``/``loads``
from this module instead of importing ``tomllib`` (or the ``tomli`` backport)
directly, so there is exactly one place that owns this compatibility concern.
When Mirror eventually drops 3.10 support, this file collapses to a plain
``from tomllib import load, loads`` and every caller stays unchanged.
"""

from __future__ import annotations

try:
    import tomllib as _toml
except ModuleNotFoundError:  # Python 3.10
    try:
        import tomli as _toml  # type: ignore[no-redef]
    except ModuleNotFoundError as exc:  # pragma: no cover - exercised only on 3.10 w/o tomli
        raise ModuleNotFoundError(
            "Parsing TOML on Python 3.10 requires the 'tomli' backport. "
            "Install it with `pip install tomli`, or run Mirror on Python "
            "3.11+ where 'tomllib' ships in the standard library."
        ) from exc

load = _toml.load
loads = _toml.loads

__all__ = ["load", "loads"]