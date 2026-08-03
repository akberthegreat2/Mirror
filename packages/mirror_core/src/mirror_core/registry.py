"""Immutable descriptor models and registries for Mirror extensions."""

from __future__ import annotations

from typing import Any

from packaging.specifiers import InvalidSpecifier, SpecifierSet
from packaging.version import InvalidVersion, Version
from pydantic import BaseModel, ConfigDict, Field

from mirror_core.exceptions import RegistryError


class CapabilityConfig(BaseModel):
    """Immutable descriptor for a capability contract."""

    model_config = ConfigDict(frozen=True)

    name: str
    api_version: str
    protocol: type | None = None
    request_model: type[BaseModel] | None = None
    result_model: type[BaseModel] | None = None
    settings_model: type[BaseModel] | str | None = None
    runner: str | None = None
    input_ports: dict[str, type[BaseModel]] = Field(default_factory=dict)
    output_ports: dict[str, type[BaseModel]] = Field(default_factory=dict)
    required_capabilities: list[str] = Field(default_factory=list)
    optional_capabilities: list[str] = Field(default_factory=list)
    signals: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def __hash__(self) -> int:
        return hash((self.name, self.api_version))


class ProviderConfig(BaseModel):
    """Immutable descriptor for a capability provider."""

    model_config = ConfigDict(frozen=True)

    name: str
    capability: str
    capability_api: str
    factory: str
    settings_model: type[BaseModel] | str | None = None
    features: list[str] = Field(default_factory=list)
    priority: int = 0
    metadata: dict[str, Any] = Field(default_factory=dict)

    def __hash__(self) -> int:
        return hash((self.name, self.capability))


class MiddlewareConfig(BaseModel):
    """Immutable descriptor for middleware."""

    model_config = ConfigDict(frozen=True)

    name: str
    factory: str
    settings_model: type[BaseModel] | str | None = None
    applies_to: list[str] | None = None
    priority: int = 0
    before: list[str] = Field(default_factory=list)
    after: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class InterfaceConfig(BaseModel):
    """Immutable descriptor for an optional external interface."""

    model_config = ConfigDict(frozen=True)

    name: str
    interface_type: str
    factory: str
    requires_capabilities: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


ExtensionDescriptor = CapabilityConfig | ProviderConfig | MiddlewareConfig | InterfaceConfig


class Registry:
    """Store extension descriptors and resolve compatible versions."""

    def __init__(self) -> None:
        self._capabilities: dict[tuple[str, str], CapabilityConfig] = {}
        self._providers: dict[tuple[str, str], ProviderConfig] = {}
        self._middleware: dict[str, MiddlewareConfig] = {}
        self._interfaces: dict[tuple[str, str], InterfaceConfig] = {}
        self._frozen = False

    def freeze(self) -> None:
        """Prevent further descriptor registration."""
        self._frozen = True

    def _ensure_mutable(self) -> None:
        if self._frozen:
            raise RegistryError("Registry is frozen")

    def register_capability(self, config: CapabilityConfig) -> None:
        self._ensure_mutable()
        self._validate_version(config.api_version, f"capability {config.name}")
        key = (config.name, config.api_version)
        if key in self._capabilities:
            raise RegistryError(f"Duplicate capability: {config.name} {config.api_version}")
        self._capabilities[key] = config

    def register_provider(self, config: ProviderConfig) -> None:
        self._ensure_mutable()
        try:
            SpecifierSet(config.capability_api)
        except InvalidSpecifier as exc:
            raise RegistryError(
                f"Invalid capability API constraint for provider {config.name}: "
                f"{config.capability_api}"
            ) from exc
        key = (config.capability, config.name)
        if key in self._providers:
            raise RegistryError(f"Duplicate provider: {config.name} for {config.capability}")
        self._providers[key] = config

    def register_middleware(self, config: MiddlewareConfig) -> None:
        self._ensure_mutable()
        if config.name in self._middleware:
            raise RegistryError(f"Duplicate middleware: {config.name}")
        self._middleware[config.name] = config

    def register_interface(self, config: InterfaceConfig) -> None:
        self._ensure_mutable()
        key = (config.name, config.interface_type)
        if key in self._interfaces:
            raise RegistryError(f"Duplicate interface: {config.name} {config.interface_type}")
        self._interfaces[key] = config

    def get_capability(self, name: str, api_version: str) -> CapabilityConfig:
        try:
            return self._capabilities[(name, api_version)]
        except KeyError as exc:
            raise RegistryError(f"Capability not found: {name} {api_version}") from exc

    def resolve_capability(self, name: str, constraint: str | None = None) -> CapabilityConfig:
        """Resolve the newest capability version satisfying an optional constraint."""
        candidates = [
            config for (cap_name, _), config in self._capabilities.items() if cap_name == name
        ]
        if not candidates:
            raise RegistryError(f"Capability not found: {name}")
        specifier = SpecifierSet(constraint or "")
        compatible = [config for config in candidates if Version(config.api_version) in specifier]
        if not compatible:
            raise RegistryError(f"No compatible version of capability {name!r} for {constraint!r}")
        return max(compatible, key=lambda config: Version(config.api_version))

    def get_provider(self, capability: str, name: str) -> ProviderConfig:
        try:
            return self._providers[(capability, name)]
        except KeyError as exc:
            raise RegistryError(f"Provider not found: {name} for {capability}") from exc

    def resolve_provider(
        self,
        capability: CapabilityConfig,
        provider_name: str | None = None,
    ) -> ProviderConfig:
        """Resolve a provider compatible with the selected capability version."""
        candidates = [
            provider
            for (cap_name, _), provider in self._providers.items()
            if cap_name == capability.name
            and (provider_name is None or provider.name == provider_name)
        ]
        compatible = [
            provider
            for provider in candidates
            if Version(capability.api_version) in SpecifierSet(provider.capability_api)
        ]
        if not compatible:
            requested = provider_name or "any provider"
            raise RegistryError(
                f"No compatible {requested} for capability "
                f"{capability.name} {capability.api_version}"
            )
        return max(compatible, key=lambda provider: (provider.priority, provider.name))

    def get_middleware(self, name: str) -> MiddlewareConfig:
        try:
            return self._middleware[name]
        except KeyError as exc:
            raise RegistryError(f"Middleware not found: {name}") from exc

    def list_capabilities(self) -> list[str]:
        return sorted(f"{name}:{version}" for name, version in self._capabilities)

    def list_providers(self) -> list[str]:
        return sorted(f"{capability}:{name}" for capability, name in self._providers)

    def list_middleware(self) -> list[str]:
        return sorted(self._middleware)

    def list_interfaces(self) -> list[str]:
        return sorted(f"{name}:{kind}" for name, kind in self._interfaces)

    @staticmethod
    def _validate_version(value: str, owner: str) -> None:
        try:
            Version(value)
        except InvalidVersion as exc:
            raise RegistryError(f"Invalid version for {owner}: {value}") from exc
