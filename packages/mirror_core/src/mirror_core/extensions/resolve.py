"""Helpers for resolving manifest import paths and metadata-backed contracts."""

from __future__ import annotations

import importlib
from typing import Any, cast

from pydantic import BaseModel

from mirror_core.extensions.errors import ExtensionError


def import_symbol(path: str) -> Any:
    """Import a symbol from a ``module:symbol`` path."""
    module_name, separator, symbol_name = path.rpartition(":")
    if not separator:
        raise ExtensionError(f"Invalid import path: {path!r}")
    try:
        module = importlib.import_module(module_name)
    except Exception as exc:
        raise ExtensionError(f"Unable to import module {module_name!r}") from exc
    try:
        return getattr(module, symbol_name)
    except AttributeError as exc:
        raise ExtensionError(
            f"Unable to resolve symbol {symbol_name!r} in {module_name!r}"
        ) from exc


def resolve_type(path: str | None) -> type[BaseModel] | None:
    """Resolve an optional ``module:Type`` path to a Pydantic model class."""
    if path is None:
        return None
    resolved = import_symbol(path)
    if not isinstance(resolved, type) or not issubclass(resolved, BaseModel):
        raise ExtensionError(f"Resolved object at {path!r} is not a Pydantic model")
    return cast(type[BaseModel], resolved)


def resolve_type_map(paths: dict[str, str]) -> dict[str, type[BaseModel]]:
    """Resolve a mapping of names to ``module:Type`` strings."""
    return {
        name: resolve_type(path) for name, path in paths.items() if path is not None
    }
