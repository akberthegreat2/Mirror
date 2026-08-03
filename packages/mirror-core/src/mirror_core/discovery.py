"""Entry-point discovery for Mirror extensions.

All extensions are discovered through a single entry point group: "mirror".
Descriptors are metadata objects, not instantiated components.
"""

from __future__ import annotations

import importlib.metadata
from collections.abc import Callable
from typing import Any, Protocol

from mirror_core.exceptions import DiscoveryError
from mirror_core.registry import (
    CapabilityConfig,
    ExtensionDescriptor,
    InterfaceConfig,
    MiddlewareConfig,
    ProviderConfig,
)


class DiscoverySource(Protocol):
    """Injectable source for discovery (allows testing with fake entry points)."""

    def iter_entry_points(self, group: str) -> list[tuple[str, Callable[[], Any]]]:
        """Return list of (name, loader) for the given entry point group."""
        ...


class DefaultDiscoverySource:
    """Default discovery source using importlib.metadata."""

    def iter_entry_points(self, group: str) -> list[tuple[str, Callable[[], Any]]]:
        eps = importlib.metadata.entry_points(group=group)
        return [(ep.name, ep.load) for ep in eps]


class DiscoveryResult:
    """Rich result of discovery operation with diagnostics."""

    def __init__(self) -> None:
        self.capabilities: list[CapabilityConfig] = []
        self.providers: list[ProviderConfig] = []
        self.middleware: list[MiddlewareConfig] = []
        self.interfaces: list[InterfaceConfig] = []
        self.errors: list[tuple[str, str]] = []  # (name, error_message)
        self.duplicates: list[tuple[str, str, list[str]]] = []  # (type, identity, names)

    @property
    def all_descriptors(self) -> list[ExtensionDescriptor]:
        return self.capabilities + self.providers + self.middleware + self.interfaces

    def has_errors(self) -> bool:
        return bool(self.errors)

    def has_duplicates(self) -> bool:
        return bool(self.duplicates)


def classify_descriptor(obj: Any) -> ExtensionDescriptor | None:
    """Classify an object as one of the descriptor types."""
    if isinstance(obj, CapabilityConfig):
        return obj
    if isinstance(obj, ProviderConfig):
        return obj
    if isinstance(obj, MiddlewareConfig):
        return obj
    if isinstance(obj, InterfaceConfig):
        return obj
    return None


def detect_duplicates(descriptors: list[ExtensionDescriptor]) -> list[tuple[str, str, list[str]]]:
    """Return list of (descriptor_type, identity, duplicated_names)."""
    seen: dict[str, list[str]] = {}
    for desc in descriptors:
        if isinstance(desc, CapabilityConfig):
            key = f"capability:{desc.name}:{desc.api_version}"
        elif isinstance(desc, ProviderConfig):
            key = f"provider:{desc.name}:{desc.capability}"
        elif isinstance(desc, MiddlewareConfig):
            key = f"middleware:{desc.name}"
        elif isinstance(desc, InterfaceConfig):
            key = f"interface:{desc.name}:{desc.interface_type}"
        else:
            continue
        seen.setdefault(key, []).append(desc.name)

    duplicates = []
    for key, names in seen.items():
        if len(names) > 1:
            parts = key.split(":")
            desc_type = parts[0]
            identity = parts[1] if len(parts) > 1 else ""
            duplicates.append((desc_type, identity, names))
    return duplicates


def discover(
    group: str = "mirror",
    source: DiscoverySource | None = None,
) -> DiscoveryResult:
    """Discover all extension descriptors in the entry point group.

    Args:
        group: Entry point group name (default: "mirror").
        source: Injectable discovery source for testing.

    Returns:
        DiscoveryResult with categorized descriptors and diagnostics.
    """
    if source is None:
        source = DefaultDiscoverySource()

    result = DiscoveryResult()

    try:
        entries = source.iter_entry_points(group)
    except Exception as e:
        raise DiscoveryError(f"Failed to read entry points: {e}", cause=e) from e

    for name, loader in entries:
        try:
            obj = loader()
        except Exception as e:
            result.errors.append((name, f"Failed to load entry point: {e}"))
            continue

        desc = classify_descriptor(obj)
        if desc is None:
            result.errors.append((name, f"Unknown descriptor type: {type(obj).__name__}"))
            continue

        if isinstance(desc, CapabilityConfig):
            result.capabilities.append(desc)
        elif isinstance(desc, ProviderConfig):
            result.providers.append(desc)
        elif isinstance(desc, MiddlewareConfig):
            result.middleware.append(desc)
        elif isinstance(desc, InterfaceConfig):
            result.interfaces.append(desc)

    # Detect duplicates across all descriptors
    result.duplicates = detect_duplicates(result.all_descriptors)

    return result
