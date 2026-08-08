"""Extension registries – one per kind, plus a manager that owns them.

All registries are immutable after freeze().
"""

from __future__ import annotations

import threading
from typing import Any, cast

from packaging.specifiers import SpecifierSet
from packaging.version import Version

from mirror_core.extensions.errors import RegistryError
from mirror_core.extensions.models import (
    CapabilityManifest,
    InterfaceManifest,
    MiddlewareManifest,
    ProviderManifest,
    StorageManifest,
)


class BaseRegistry:
    """Base class for a registry of a specific extension kind."""

    def __init__(self) -> None:
        self._items: dict[str, Any] = {}
        self._frozen = False
        self._lock = threading.RLock()

    def register(self, manifest: Any) -> None:
        """Register a manifest (must be of the correct kind)."""
        with self._lock:
            if self._frozen:
                raise RegistryError("Cannot register: registry is frozen.")
            if manifest.extension_id in self._items:
                raise RegistryError(f"Duplicate extension ID: {manifest.extension_id}")
            self._items[manifest.extension_id] = manifest

    def get(self, extension_id: str) -> Any:
        """Get a manifest by ID."""
        with self._lock:
            try:
                return self._items[extension_id]
            except KeyError:
                raise RegistryError(f"Extension not found: {extension_id}") from None

    def list(self) -> list[Any]:
        """Return all manifests (as a list)."""
        with self._lock:
            return list(self._items.values())

    def freeze(self) -> None:
        """Make the registry immutable."""
        with self._lock:
            self._frozen = True

    @property
    def frozen(self) -> bool:
        """Whether the registry is frozen."""
        return self._frozen


class CapabilityRegistry(BaseRegistry):
    """Registry for capability extensions."""

    def _matches(self, manifest: CapabilityManifest, name: str, api_version: str | None) -> bool:
        return manifest.name == name and (api_version is None or manifest.api_version == api_version)

    def get_capability(self, capability_name: str, api_version: str | None = None) -> CapabilityManifest:
        candidates = self.list_capabilities()
        if api_version is not None:
            for manifest in candidates:
                if self._matches(manifest, capability_name, api_version):
                    return manifest
            raise RegistryError(f"Capability not found: {capability_name!r} ({api_version!r})")

        matching = [manifest for manifest in candidates if manifest.name == capability_name]
        if not matching:
            raise RegistryError(f"Capability not found: {capability_name!r}")
        return max(matching, key=lambda manifest: Version(str(manifest.api_version)))

    def list_capabilities(self) -> list[CapabilityManifest]:
        return cast(list[CapabilityManifest], self.list())


class ProviderRegistry(BaseRegistry):
    """Registry for provider extensions."""

    def get_provider(self, capability_name: str, provider_name: str | None = None) -> ProviderManifest:
        candidates = self.get_providers_for_capability(capability_name)
        if provider_name is not None:
            for manifest in candidates:
                if manifest.name == provider_name or manifest.extension_id == provider_name:
                    return manifest
            raise RegistryError(f"Provider not found: {capability_name!r}/{provider_name!r}")

        if not candidates:
            raise RegistryError(f"Provider not found for capability: {capability_name!r}")
        return max(candidates, key=lambda manifest: (manifest.priority, manifest.name))

    def list_providers(self) -> list[ProviderManifest]:
        return cast(list[ProviderManifest], self.list())

    def get_providers_for_capability(self, capability_name: str) -> list[ProviderManifest]:
        """Return all providers that implement the given capability name."""
        with self._lock:
            return cast(
                list[ProviderManifest],
                [p for p in self._items.values() if p.capability == capability_name],
            )


class InterfaceRegistry(BaseRegistry):
    """Registry for interface extensions."""

    def get_interface(self, extension_id: str) -> InterfaceManifest:
        return cast(InterfaceManifest, self.get(extension_id))

    def list_interfaces(self) -> list[InterfaceManifest]:
        return cast(list[InterfaceManifest], self.list())


class MiddlewareRegistry(BaseRegistry):
    """Registry for middleware extensions."""

    def get_middleware(self, extension_id: str) -> MiddlewareManifest:
        return cast(MiddlewareManifest, self.get(extension_id))

    def list_middleware(self) -> list[MiddlewareManifest]:
        return cast(list[MiddlewareManifest], self.list())


class StorageRegistry(BaseRegistry):
    """Registry for storage extensions."""

    def get_storage(self, extension_id: str) -> StorageManifest:
        return cast(StorageManifest, self.get(extension_id))

    def list_storage(self) -> list[StorageManifest]:
        return cast(list[StorageManifest], self.list())


class ExtensionRegistryManager:
    """Manages all extension registries and provides a unified interface."""

    def __init__(self) -> None:
        self.capabilities = CapabilityRegistry()
        self.providers = ProviderRegistry()
        self.interfaces = InterfaceRegistry()
        self.middleware = MiddlewareRegistry()
        self.storage = StorageRegistry()
        self._frozen = False

    def register(self, manifest: Any) -> None:
        """Register a manifest in the appropriate registry based on its kind."""
        if self._frozen:
            raise RegistryError("Cannot register: registry manager is frozen.")

        if isinstance(manifest, CapabilityManifest):
            self.capabilities.register(manifest)
        elif isinstance(manifest, ProviderManifest):
            self.providers.register(manifest)
        elif isinstance(manifest, InterfaceManifest):
            self.interfaces.register(manifest)
        elif isinstance(manifest, MiddlewareManifest):
            self.middleware.register(manifest)
        elif isinstance(manifest, StorageManifest):
            self.storage.register(manifest)
        else:
            raise RegistryError(f"Unknown manifest type: {type(manifest)}")

    def register_capability(self, manifest: CapabilityManifest) -> None:
        self.register(manifest)

    def register_provider(self, manifest: ProviderManifest) -> None:
        self.register(manifest)

    def register_interface(self, manifest: InterfaceManifest) -> None:
        self.register(manifest)

    def register_middleware(self, manifest: MiddlewareManifest) -> None:
        self.register(manifest)

    def register_storage(self, manifest: StorageManifest) -> None:
        self.register(manifest)

    def freeze(self) -> None:
        """Freeze all registries."""
        if self._frozen:
            return
        self.capabilities.freeze()
        self.providers.freeze()
        self.interfaces.freeze()
        self.middleware.freeze()
        self.storage.freeze()
        self._frozen = True

    @property
    def frozen(self) -> bool:
        return self._frozen

    def get_extension(self, extension_id: str) -> Any:
        """Look up an extension by ID across all registries."""
        for registry in (
            self.capabilities,
            self.providers,
            self.interfaces,
            self.middleware,
            self.storage,
        ):
            try:
                return registry.get(extension_id)
            except RegistryError:
                continue
        raise RegistryError(f"Extension not found: {extension_id}")

    def resolve_capability(self, capability_name: str, constraint: str | None = None) -> CapabilityManifest:
        candidates = [manifest for manifest in self.capabilities.list_capabilities() if manifest.name == capability_name]
        if not candidates:
            raise RegistryError(f"Capability not found: {capability_name!r}")
        if constraint is not None:
            specifier = SpecifierSet(constraint)
            candidates = [manifest for manifest in candidates if Version(str(manifest.api_version)) in specifier]
        if not candidates:
            constraint_text = constraint if constraint is not None else "any version"
            raise RegistryError(f"Capability {capability_name!r} does not satisfy {constraint_text!r}")
        return max(candidates, key=lambda manifest: Version(str(manifest.api_version)))

    def resolve_provider(
        self,
        capability: CapabilityManifest,
        provider_name: str | None = None,
    ) -> ProviderManifest:
        candidates = [provider for provider in self.providers.list_providers() if provider.capability == capability.name and (provider_name is None or provider.name == provider_name or provider.extension_id == provider_name) and Version(str(capability.api_version)) in SpecifierSet(provider.capability_api)]
        if not candidates:
            requested = provider_name or "any provider"
            raise RegistryError(f"No compatible {requested} for capability {capability.name} {capability.api_version}")
        return max(candidates, key=lambda provider: (provider.priority, provider.name))

    def get_capability(self, capability_name: str, api_version: str | None = None) -> CapabilityManifest:
        return self.capabilities.get_capability(capability_name, api_version)

    def get_provider(self, capability_name: str, provider_name: str | None = None) -> ProviderManifest:
        return self.providers.get_provider(capability_name, provider_name)

    def get_interface(self, extension_id: str) -> InterfaceManifest:
        return self.interfaces.get_interface(extension_id)

    def get_middleware(self, extension_id: str) -> MiddlewareManifest:
        return self.middleware.get_middleware(extension_id)

    def get_storage(self, extension_id: str) -> StorageManifest:
        return self.storage.get_storage(extension_id)

    def list_capabilities(self) -> list[CapabilityManifest]:
        return self.capabilities.list_capabilities()

    def list_providers(self) -> list[ProviderManifest]:
        return self.providers.list_providers()

    def list_providers_for_capability(self, capability_name: str) -> list[ProviderManifest]:
        return self.providers.get_providers_for_capability(capability_name)

    def list_interfaces(self) -> list[InterfaceManifest]:
        return self.interfaces.list_interfaces()

    def list_middleware(self) -> list[MiddlewareManifest]:
        return self.middleware.list_middleware()

    def list_storage(self) -> list[StorageManifest]:
        return self.storage.list_storage()
