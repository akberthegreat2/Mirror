"""Mirror Extension System – manifests, discovery, registries, validation.

This module provides the foundation for all pluggable components in Mirror.
"""

from mirror_core.extensions.discovery import discover_extensions
from mirror_core.extensions.errors import (
    DiscoveryError,
    ExtensionError,
    RegistryError,
    ValidationError,
)
from mirror_core.extensions.models import (
    CapabilityManifest,
    Dependency,
    ExtensionKind,
    ExtensionManifest,
    InterfaceManifest,
    LifecycleInfo,
    MiddlewareManifest,
    ProviderManifest,
    StorageManifest,
)
from mirror_core.extensions.registry import (
    CapabilityRegistry,
    ExtensionRegistryManager,
    InterfaceRegistry,
    MiddlewareRegistry,
    ProviderRegistry,
    StorageRegistry,
)
from mirror_core.extensions.validation import validate_manifests

__all__ = [
    "CapabilityManifest",
    "CapabilityRegistry",
    "Dependency",
    "DiscoveryError",
    "ExtensionError",
    "ExtensionKind",
    "ExtensionManifest",
    "ExtensionRegistryManager",
    "InterfaceManifest",
    "InterfaceRegistry",
    "LifecycleInfo",
    "MiddlewareManifest",
    "MiddlewareRegistry",
    "ProviderManifest",
    "ProviderRegistry",
    "RegistryError",
    "StorageManifest",
    "StorageRegistry",
    "ValidationError",
    "discover_extensions",
    "validate_manifests",
]
