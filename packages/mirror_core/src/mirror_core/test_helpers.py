"""Test helpers for building manifest-native extension fixtures."""

from __future__ import annotations

from typing import Any

from mirror_core.extensions.models import (
    CapabilityManifest,
    Dependency,
    ExtensionKind,
    InterfaceManifest,
    MiddlewareManifest,
    ProviderManifest,
)
from mirror_core.extensions.registry import ExtensionRegistryManager


def _type_path(value: object | str | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, type):
        return f"{value.__module__}:{value.__qualname__}"
    raise TypeError(f"Expected a type or import path, got {type(value).__name__}")


def dependency(*, name: str, version: str | None = None) -> Dependency:
    return Dependency(
        target=name,
        target_kind=ExtensionKind.CAPABILITY,
        version_constraint=version or ">=0.0.0",
        required=True,
    )


def capability_manifest(
    *,
    extension_id: str,
    name: str | None = None,
    api_version: str,
    protocol: object | str | None = None,
    request_model: object | str | None = None,
    result_model: object | str | None = None,
    settings_model: object | str | None = None,
    runner: str | None = None,
    input_ports: dict[str, object | str] | None = None,
    output_ports: dict[str, object | str] | None = None,
    dependencies: list[Dependency] | None = None,
    metadata: dict[str, Any] | None = None,
) -> CapabilityManifest:
    meta = dict(metadata or {})
    if request_model is not None:
        meta["request_model"] = _type_path(request_model)
    if result_model is not None:
        meta["result_model"] = _type_path(result_model)
    resolved_name = name or extension_id
    return CapabilityManifest(
        extension_id=extension_id,
        name=resolved_name,
        description=meta.get("description", meta.get("summary", "")),
        version="0.1.0",
        package_name="tests",
        api_version=api_version,
        settings_model=_type_path(settings_model),
        protocol=_type_path(protocol),
        runner=runner,
        input_ports={port: _type_path(tp) for port, tp in (input_ports or {}).items()},
        output_ports={port: _type_path(tp) for port, tp in (output_ports or {}).items()},
        dependencies=dependencies or [],
        metadata=meta,
    )


def provider_manifest(
    *,
    extension_id: str,
    name: str | None = None,
    capability: str,
    capability_api: str,
    factory: str,
    settings_model: object | str | None = None,
    features: list[str] | None = None,
    priority: int = 0,
    metadata: dict[str, Any] | None = None,
) -> ProviderManifest:
    meta = dict(metadata or {})
    if features:
        meta.setdefault("features", list(features))
    resolved_name = name or extension_id.split("-")[-1]
    return ProviderManifest(
        extension_id=extension_id,
        name=resolved_name,
        description=meta.get("description", ""),
        version="0.1.0",
        package_name="tests",
        capability=capability,
        capability_api=capability_api,
        factory=factory,
        settings_model=_type_path(settings_model),
        priority=priority,
        metadata=meta,
    )


def middleware_manifest(
    *,
    extension_id: str,
    name: str | None = None,
    factory: str,
    settings_model: object | str | None = None,
    applies_to: list[str] | None = None,
    priority: int = 0,
    before: list[str] | None = None,
    after: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
) -> MiddlewareManifest:
    meta = dict(metadata or {})
    resolved_name = name or extension_id
    return MiddlewareManifest(
        extension_id=extension_id,
        name=resolved_name,
        description=meta.get("description", ""),
        version="0.1.0",
        package_name="tests",
        factory=factory,
        settings_model=_type_path(settings_model),
        applies_to=applies_to,
        priority=priority,
        before=before or [],
        after=after or [],
        metadata=meta,
    )


def interface_manifest(
    *,
    extension_id: str,
    name: str | None = None,
    interface_type: str,
    factory: str,
    requires_capabilities: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
) -> InterfaceManifest:
    meta = dict(metadata or {})
    resolved_name = name or extension_id
    return InterfaceManifest(
        extension_id=extension_id,
        name=resolved_name,
        description=meta.get("description", ""),
        version="0.1.0",
        package_name="tests",
        interface_type=interface_type,
        factory=factory,
        requires_capabilities=requires_capabilities or [],
        metadata=meta,
    )


def registry_manager() -> ExtensionRegistryManager:
    return ExtensionRegistryManager()
