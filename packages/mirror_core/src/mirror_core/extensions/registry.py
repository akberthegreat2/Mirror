"""Extension registries – one per kind, plus a manager that owns them.

All registries are immutable after freeze().
"""

from __future__ import annotations

import threading
from typing import Any, cast

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

    def get_capability(self, extension_id: str) -> CapabilityManifest:
        return cast(CapabilityManifest, self.get(extension_id))

    def list_capabilities(self) -> list[CapabilityManifest]:
        return cast(list[CapabilityManifest], self.list())


class ProviderRegistry(BaseRegistry):
    """Registry for provider extensions."""

    def get_provider(self, extension_id: str) -> ProviderManifest:
        return cast(ProviderManifest, self.get(extension_id))

    def list_providers(self) -> list[ProviderManifest]:
        return cast(list[ProviderManifest], self.list())

    def get_providers_for_capability(
        self, capability_id: str
    ) -> list[ProviderManifest]:
        """Return all providers that implement the given capability."""
        with self._lock:
            return cast(
                list[ProviderManifest],
                [p for p in self._items.values() if p.capability == capability_id],
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

    def get_capability(self, extension_id: str) -> CapabilityManifest:
        return self.capabilities.get_capability(extension_id)

    def get_provider(self, extension_id: str) -> ProviderManifest:
        return self.providers.get_provider(extension_id)

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

    def list_providers_for_capability(
        self, capability_id: str
    ) -> list[ProviderManifest]:
        return self.providers.get_providers_for_capability(capability_id)

    def list_interfaces(self) -> list[InterfaceManifest]:
        return self.interfaces.list_interfaces()

    def list_middleware(self) -> list[MiddlewareManifest]:
        return self.middleware.list_middleware()

    def list_storage(self) -> list[StorageManifest]:
        return self.storage.list_storage()
