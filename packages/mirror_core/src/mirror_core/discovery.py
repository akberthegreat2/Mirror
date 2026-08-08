"""Entry-point discovery for Mirror extensions.

The canonical extension system discovers manifests from the manifest entry
point groups and classifies them by manifest kind.
"""

from __future__ import annotations

from typing import Any, Protocol

from mirror_core.exceptions import DiscoveryError
from mirror_core.extensions.discovery import discover_extensions
from mirror_core.extensions.models import (
    CapabilityManifest,
    ExtensionManifest,
    InterfaceManifest,
    MiddlewareManifest,
    ProviderManifest,
)
from mirror_core.extensions.validation import validate_manifests


class DiscoverySource(Protocol):
    """Injectable source for discovery (allows testing with fake entry points)."""

    def discover(self) -> tuple[list[Any], list[tuple[str, str]]]:
        """Return raw extension objects and load errors."""
        ...


class DefaultDiscoverySource:
    """Default discovery source using importlib.metadata via canonical groups."""

    def discover(self) -> tuple[list[Any], list[tuple[str, str]]]:
        return discover_extensions()


class DiscoveryResult:
    """Rich result of discovery operation with diagnostics."""

    def __init__(self) -> None:
        self.capabilities: list[CapabilityManifest] = []
        self.providers: list[ProviderManifest] = []
        self.middleware: list[MiddlewareManifest] = []
        self.interfaces: list[InterfaceManifest] = []
        self.errors: list[tuple[str, str]] = []
        self.duplicates: list[tuple[str, str, list[str]]] = []

    @property
    def all_manifests(self) -> list[ExtensionManifest]:
        return [
            *self.capabilities,
            *self.providers,
            *self.middleware,
            *self.interfaces,
        ]

    def has_errors(self) -> bool:
        return bool(self.errors)

    def has_duplicates(self) -> bool:
        return bool(self.duplicates)


def classify_manifest(obj: Any) -> ExtensionManifest | None:
    """Classify an object as one of the manifest types."""
    if isinstance(obj, ExtensionManifest):
        return obj
    return None


def discover(source: DiscoverySource | None = None) -> DiscoveryResult:
    """Discover all extension manifests from the canonical groups."""
    if source is None:
        source = DefaultDiscoverySource()

    result = DiscoveryResult()

    try:
        manifests, errors = source.discover()
    except Exception as exc:
        raise DiscoveryError(f"Failed to read entry points: {exc}", cause=exc) from exc

    result.errors.extend(errors)

    classified: list[ExtensionManifest] = []
    for obj in manifests:
        desc = classify_manifest(obj)
        if desc is None:
            result.errors.append(
                (
                    getattr(
                        obj, "extension_id", getattr(obj, "name", type(obj).__name__)
                    ),
                    f"Unknown manifest type: {type(obj).__name__}",
                )
            )
            continue
        classified.append(desc)

    valid, validation_errors = validate_manifests(classified)
    result.errors.extend(validation_errors)

    duplicate_ids = sorted(
        {
            extension_id
            for extension_id, message in validation_errors
            if message.startswith("Duplicate extension ID:")
        }
    )
    for extension_id in duplicate_ids:
        result.duplicates.append(("extension", extension_id, [extension_id]))

    for manifest in valid:
        if isinstance(manifest, CapabilityManifest):
            result.capabilities.append(manifest)
        elif isinstance(manifest, ProviderManifest):
            result.providers.append(manifest)
        elif isinstance(manifest, MiddlewareManifest):
            result.middleware.append(manifest)
        elif isinstance(manifest, InterfaceManifest):
            result.interfaces.append(manifest)

    return result
