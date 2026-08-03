"""Descriptor registry for Mirror extensions.

The registry stores immutable descriptors discovered via entry points.
It does not instantiate components.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from mirror_core.exceptions import RegistryError


# Descriptor Models (immutable)


class CapabilityConfig(BaseModel):
    """Immutable descriptor for a capability.

    Single-port capabilities may use request_model and result_model
    as shorthand. Multi-port capabilities must use input_ports and
    output_ports (maps of port name → resource type).

    The runner must support both patterns.
    """

    model_config = ConfigDict(frozen=True)

    name: str
    api_version: str
    protocol: type | None = None
    request_model: type[BaseModel] | None = None
    result_model: type[BaseModel] | None = None
    settings_model: type[BaseModel] | str | None = None
    runner: str | None = None  # import path
    input_ports: dict[str, type[BaseModel]] = Field(default_factory=dict)
    output_ports: dict[str, type[BaseModel]] = Field(default_factory=dict)
    required_capabilities: list[str] = Field(default_factory=list)
    optional_capabilities: list[str] = Field(default_factory=list)
    signals: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def __hash__(self) -> int:
        return hash((self.name, self.api_version))


class ProviderConfig(BaseModel):
    """Immutable descriptor for a provider."""

    model_config = ConfigDict(frozen=True)

    name: str
    capability: str
    capability_api: str  # version constraint like "~=1.0"
    factory: str  # import path
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
    applies_to: list[str] | None = None  # capability names; None = all
    ordering_constraints: dict[str, str] | None = None  # "before", "after"
    metadata: dict[str, Any] = Field(default_factory=dict)


class InterfaceConfig(BaseModel):
    """Immutable descriptor for optional interfaces (CLI, admin, REST)."""

    model_config = ConfigDict(frozen=True)

    name: str
    interface_type: str  # "cli", "admin", "rest", "graphql"
    factory: str
    requires_capabilities: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


ExtensionDescriptor = CapabilityConfig | ProviderConfig | MiddlewareConfig | InterfaceConfig


class Registry:
    """Stores discovered descriptors and provides lookup."""

    def __init__(self) -> None:
        self._capabilities: dict[str, CapabilityConfig] = {}
        self._providers: dict[str, ProviderConfig] = {}
        self._middleware: dict[str, MiddlewareConfig] = {}
        self._interfaces: dict[str, InterfaceConfig] = {}

    def register_capability(self, config: CapabilityConfig) -> None:
        key = f"{config.name}:{config.api_version}"
        if key in self._capabilities:
            raise RegistryError(f"Duplicate capability: {config.name} {config.api_version}")
        self._capabilities[key] = config

    def register_provider(self, config: ProviderConfig) -> None:
        key = f"{config.capability}:{config.name}"
        if key in self._providers:
            raise RegistryError(f"Duplicate provider: {config.name} for {config.capability}")
        self._providers[key] = config

    def register_middleware(self, config: MiddlewareConfig) -> None:
        if config.name in self._middleware:
            raise RegistryError(f"Duplicate middleware: {config.name}")
        self._middleware[config.name] = config

    def register_interface(self, config: InterfaceConfig) -> None:
        key = f"{config.name}:{config.interface_type}"
        if key in self._interfaces:
            raise RegistryError(f"Duplicate interface: {config.name} {config.interface_type}")
        self._interfaces[key] = config

    def get_capability(self, name: str, api_version: str) -> CapabilityConfig:
        key = f"{name}:{api_version}"
        if key not in self._capabilities:
            raise RegistryError(f"Capability not found: {name} {api_version}")
        return self._capabilities[key]

    def get_provider(self, capability: str, name: str) -> ProviderConfig:
        key = f"{capability}:{name}"
        if key not in self._providers:
            raise RegistryError(f"Provider not found: {name} for {capability}")
        return self._providers[key]

    def get_middleware(self, name: str) -> MiddlewareConfig:
        if name not in self._middleware:
            raise RegistryError(f"Middleware not found: {name}")
        return self._middleware[name]

    def list_capabilities(self) -> list[str]:
        return sorted(self._capabilities.keys())

    def list_providers(self) -> list[str]:
        return sorted(self._providers.keys())

    def list_middleware(self) -> list[str]:
        return sorted(self._middleware.keys())

    def list_interfaces(self) -> list[str]:
        return sorted(self._interfaces.keys())