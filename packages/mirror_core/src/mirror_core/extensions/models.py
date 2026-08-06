"""Data models for extension manifests.

All extension manifests are Pydantic models for validation and serialization.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from packaging.specifiers import SpecifierSet
from pydantic import BaseModel, ConfigDict, Field, field_validator


class ExtensionKind(str, Enum):
    """The primary kind of an extension."""

    CAPABILITY = "capability"
    PROVIDER = "provider"
    INTERFACE = "interface"
    MIDDLEWARE = "middleware"
    STORAGE = "storage"


class LifecycleInfo(BaseModel):
    """Metadata about an extension's lifecycle requirements."""

    model_config = ConfigDict(frozen=True)

    supports_setup: bool = False
    supports_teardown: bool = False
    # Optional description for documentation
    description: str = ""


class Dependency(BaseModel):
    """A dependency on another extension (typically a capability)."""

    model_config = ConfigDict(frozen=True)

    target: str  # extension_id of the dependency
    target_kind: ExtensionKind  # usually CAPABILITY, but could be other
    version_constraint: str = ">=0.0.0"  # specifier string, e.g., ">=1.0,<2.0"
    required: bool = True

    @field_validator("version_constraint")
    def validate_specifier(cls, v: str) -> str:
        """Ensure the version constraint is a valid specifier set."""
        try:
            SpecifierSet(v)
        except Exception as exc:
            raise ValueError(f"Invalid version constraint: {v}") from exc
        return v


class ExtensionManifest(BaseModel):
    """Base manifest for any extension.

    All extension manifests share these fields.
    """

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=False)

    # Identity
    extension_id: str = Field(..., description="Unique identifier for this extension")
    name: str = Field(..., description="Human‑readable name")
    description: str = ""
    version: str = Field(..., description="Semantic version of this extension")
    package_name: str | None = Field(
        None, description="Distribution package name (for diagnostics)"
    )
    kind: ExtensionKind

    # Compatibility
    api_version: str = Field("1.0", description="API version of the extension contract")
    requires_core: str = Field(">=0.1.0", description="Mirror Core version constraint")

    # Lifecycle
    lifecycle: LifecycleInfo = Field(default_factory=LifecycleInfo)

    # Dependencies
    dependencies: list[Dependency] = Field(default_factory=list)

    # Settings
    settings_model: str | None = Field(
        None,
        description="Import path to a Pydantic settings model (e.g., 'module:Model')",
    )

    # Metadata (free‑form, for documentation)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def __hash__(self) -> int:
        return hash(self.extension_id)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ExtensionManifest):
            return NotImplemented
        return self.extension_id == other.extension_id


class CapabilityManifest(ExtensionManifest):
    """Manifest for a capability extension."""

    kind: ExtensionKind = ExtensionKind.CAPABILITY

    # Capability-specific fields
    protocol: str | None = Field(
        None, description="Import path to the protocol/interface class"
    )
    runner: str | None = Field(None, description="Import path to the runner function")
    input_ports: dict[str, str] = Field(
        default_factory=dict,
        description="Mapping from port name to Python type import path",
    )
    output_ports: dict[str, str] = Field(
        default_factory=dict,
        description="Mapping from port name to Python type import path",
    )


class ProviderManifest(ExtensionManifest):
    """Manifest for a provider extension."""

    kind: ExtensionKind = ExtensionKind.PROVIDER

    # Provider-specific fields
    capability: str = Field(..., description="Capability extension_id this implements")
    implements_version: str = Field(
        ">=1.0,<2.0",
        description="Version constraint for the capability API this provider supports",
    )
    factory: str = Field(..., description="Import path to the provider factory/class")
    priority: int = Field(
        0, description="Priority (higher = selected first when no preference)"
    )
    health_check: str | None = Field(
        None,
        description="Optional import path to an async health check callable",
    )


class InterfaceManifest(ExtensionManifest):
    """Manifest for an interface extension (CLI, REST, GraphQL, etc.)."""

    kind: ExtensionKind = ExtensionKind.INTERFACE

    # Interface-specific
    entry_point: str | None = Field(
        None,
        description="Import path to the interface entry point (e.g., CLI command group)",
    )


class MiddlewareManifest(ExtensionManifest):
    """Manifest for a middleware extension."""

    kind: ExtensionKind = ExtensionKind.MIDDLEWARE

    # Middleware-specific
    factory: str = Field(..., description="Import path to the middleware factory")
    applies_to: list[str] | None = Field(
        None,
        description="List of capability IDs this middleware applies to; None means global",
    )
    after: list[str] = Field(
        default_factory=list,
        description="List of middleware IDs that must run before this one",
    )
    before: list[str] = Field(
        default_factory=list,
        description="List of middleware IDs that must run after this one",
    )


class StorageManifest(ExtensionManifest):
    """Manifest for a storage backend extension."""

    kind: ExtensionKind = ExtensionKind.STORAGE

    # Storage-specific
    factory: str = Field(..., description="Import path to the storage factory")
    supports: list[str] = Field(
        default_factory=list,
        description="List of storage contracts this implements (e.g., 'metadata', 'blob')",
    )
