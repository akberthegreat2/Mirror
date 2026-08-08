"""Data models for extension manifests.

All shipped extensions publish manifests. The runtime may carry either direct
Python objects or import-path strings while the migration finishes, but the
published contract is the manifest model itself.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from packaging.specifiers import SpecifierSet
from pydantic import BaseModel, ConfigDict, Field, model_validator


class ExtensionKind(str, Enum):
    """The primary kind of an extension."""

    CAPABILITY = "capability"
    PROVIDER = "provider"
    INTERFACE = "interface"
    MIDDLEWARE = "middleware"
    STORAGE = "storage"


class LifecycleInfo(BaseModel):
    """Metadata about an extension's lifecycle requirements."""

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    supports_setup: bool = False
    supports_teardown: bool = False
    description: str = ""


class Dependency(BaseModel):
    """A dependency on another extension (typically a capability)."""

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True, populate_by_name=True)

    target: str = Field(..., alias="name")
    target_kind: ExtensionKind = ExtensionKind.CAPABILITY
    version_constraint: str = Field(">=0.0.0", alias="version")
    required: bool = True

    @model_validator(mode="after")
    def validate_specifier(self) -> Dependency:
        """Ensure the version constraint is a valid specifier set."""
        if self.target is None:
            raise ValueError("Dependency target is required")
        SpecifierSet(self.version_constraint)
        return self


class ExtensionManifest(BaseModel):
    """Base manifest for any extension."""

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    extension_id: str = Field(default="", description="Unique identifier for this extension")
    name: str = Field(..., description="Human-readable name")
    description: str = ""
    version: str = Field("0.1.0", description="Semantic version of this extension")
    package_name: str | None = Field(None, description="Distribution package name (for diagnostics)")
    kind: ExtensionKind

    api_version: str = Field("1.0", description="API version of the extension contract")
    requires_core: str = Field(">=0.1.0", description="Mirror Core version constraint")

    lifecycle: LifecycleInfo = Field(default_factory=LifecycleInfo)
    dependencies: list[Dependency] = Field(default_factory=list)
    settings_model: Any | str | None = Field(None, description="Settings model object or import path")
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def default_extension_id(self) -> ExtensionManifest:
        if not self.extension_id:
            object.__setattr__(self, "extension_id", self.name)
        return self

    def __hash__(self) -> int:
        return hash(self.extension_id)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ExtensionManifest):
            return NotImplemented
        return self.extension_id == other.extension_id


class CapabilityManifest(ExtensionManifest):
    """Manifest for a capability extension."""

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    kind: ExtensionKind = ExtensionKind.CAPABILITY
    protocol: Any | str | None = Field(None, description="Protocol/interface class or import path")
    request_model: Any | str | None = Field(None, description="Request model class or import path")
    result_model: Any | str | None = Field(None, description="Result model class or import path")
    runner: str | None = Field(None, description="Import path to the runner function")
    input_ports: dict[str, Any | str] = Field(
        default_factory=dict,
        description="Mapping from port name to Python type or import path",
    )
    output_ports: dict[str, Any | str] = Field(
        default_factory=dict,
        description="Mapping from port name to Python type or import path",
    )

    @model_validator(mode="after")
    def default_extension_id(self) -> CapabilityManifest:
        if not self.extension_id:
            object.__setattr__(self, "extension_id", f"{self.name}:{self.api_version}")
        return self


class ProviderManifest(ExtensionManifest):
    """Manifest for a provider extension."""

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    kind: ExtensionKind = ExtensionKind.PROVIDER
    capability: str = Field(..., description="Capability this provider implements")
    capability_api: str = Field(
        ">=1.0,<2.0",
        description="Version constraint for the capability API this provider supports",
    )
    factory: str = Field(..., description="Import path to the provider factory/class")
    features: list[str] = Field(default_factory=list)
    priority: int = Field(0, description="Priority (higher = selected first)")
    health_check: str | None = Field(
        None,
        description="Optional import path to an async health check callable",
    )

    @model_validator(mode="after")
    def default_extension_id(self) -> ProviderManifest:
        if not self.extension_id:
            object.__setattr__(self, "extension_id", f"{self.capability}:{self.name}")
        return self


class InterfaceManifest(ExtensionManifest):
    """Manifest for an interface extension (CLI, REST, GraphQL, etc.)."""

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    kind: ExtensionKind = ExtensionKind.INTERFACE
    interface_type: str = Field(..., description="Interface kind, e.g. 'cli'")
    factory: str = Field(..., description="Import path to the interface entry point")
    requires_capabilities: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def default_extension_id(self) -> InterfaceManifest:
        if not self.extension_id:
            object.__setattr__(self, "extension_id", f"{self.interface_type}:{self.name}")
        return self


class MiddlewareManifest(ExtensionManifest):
    """Manifest for a middleware extension."""

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    kind: ExtensionKind = ExtensionKind.MIDDLEWARE
    factory: str = Field(..., description="Import path to the middleware factory")
    applies_to: list[str] | None = Field(
        None,
        description="List of capability IDs this middleware applies to; None means global",
    )
    after: list[str] = Field(default_factory=list)
    before: list[str] = Field(default_factory=list)
    priority: int = Field(0)


class StorageManifest(ExtensionManifest):
    """Manifest for a storage backend extension."""

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    kind: ExtensionKind = ExtensionKind.STORAGE
    factory: str = Field(..., description="Import path to the storage factory")
    supports: list[str] = Field(default_factory=list)
