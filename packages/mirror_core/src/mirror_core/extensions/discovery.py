"""Discovery of extension manifests from entry points."""

from __future__ import annotations

import importlib.metadata
from typing import Any

from mirror_core.extensions.models import (
    CapabilityManifest,
    ExtensionManifest,
    InterfaceManifest,
    MiddlewareManifest,
    ProviderManifest,
    StorageManifest,
)

# Mapping from entry point group to expected manifest type
ENTRY_POINT_GROUP_MAP = {
    "mirror.capabilities": CapabilityManifest,
    "mirror.providers": ProviderManifest,
    "mirror.interfaces": InterfaceManifest,
    "mirror.middleware": MiddlewareManifest,
    "mirror.storage": StorageManifest,
}


def discover_extensions(
    groups: list[str] | None = None,
) -> tuple[list[ExtensionManifest], list[tuple[str, str]]]:
    """Discover extension manifests from entry point groups.

    Args:
        groups: List of entry point groups to scan. If None, scans all known groups.

    Returns:
        A tuple of (manifests, errors) where errors are (entry_point_name, error_message).

    Raises:
        DiscoveryError: If a fatal error occurs (e.g., import error that cannot be skipped).
    """
    if groups is None:
        groups = list(ENTRY_POINT_GROUP_MAP.keys())

    manifests: list[ExtensionManifest] = []
    errors: list[tuple[str, str]] = []

    for group in groups:
        expected_type = ENTRY_POINT_GROUP_MAP.get(group)
        if expected_type is None:
            errors.append((group, f"Unknown entry point group: {group}"))
            continue

        try:
            entry_points = importlib.metadata.entry_points(group=group)
        except Exception as exc:  # noqa: BLE001
            errors.append((group, f"Failed to read entry points: {exc}"))
            continue

        for ep in entry_points:
            try:
                obj: Any = ep.load()
            except Exception as exc:  # noqa: BLE001
                errors.append((ep.name, f"Failed to load entry point: {exc}"))
                continue

            # If the object is callable, call it (allows lazy manifests)
            if callable(obj) and not isinstance(obj, type):
                try:
                    obj = obj()
                except Exception as exc:  # noqa: BLE001
                    errors.append((ep.name, f"Callable manifest failed: {exc}"))
                    continue

            # Validate type
            if not isinstance(obj, expected_type):
                errors.append(
                    (
                        ep.name,
                        f"Expected {expected_type.__name__}, got {type(obj).__name__}",
                    )
                )
                continue

            manifests.append(obj)

    return manifests, errors
