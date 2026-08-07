"""Shared import-resolution helpers for manifest-native runtime code."""

from __future__ import annotations

import importlib
from typing import Any

from pydantic import BaseModel

from mirror_core.exceptions import ApplicationError


class EmptySettings(BaseModel):
    """Settings model used when a component declares no configuration."""


def import_symbol(path: str) -> Any:
    """Import a symbol from a ``module:symbol`` path."""
    module_name, separator, symbol_name = path.rpartition(":")
    if not separator:
        raise ApplicationError(f"Invalid import path: {path!r}")
    try:
        return getattr(importlib.import_module(module_name), symbol_name)
    except (ImportError, AttributeError) as exc:
        raise ApplicationError(f"Unable to import {path!r}", cause=exc) from exc


def resolve_model(value: Any | str | None) -> type[BaseModel]:
    """Resolve an optional Pydantic model value."""
    if value is None:
        return EmptySettings
    resolved = import_symbol(value) if isinstance(value, str) else value
    if not isinstance(resolved, type) or not issubclass(resolved, BaseModel):
        raise ApplicationError("Component settings model must be a Pydantic model")
    return resolved


def resolve_type(value: Any | str | None) -> Any | None:
    """Resolve a possibly-import-path type or object.

    Direct Python objects are returned unchanged. Strings are treated as
    ``module:attribute`` import paths.
    """
    if value is None:
        return None
    if isinstance(value, str):
        return import_symbol(value)
    return value
