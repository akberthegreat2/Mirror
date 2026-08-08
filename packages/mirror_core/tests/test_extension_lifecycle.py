"""Tests for the explicit extension lifecycle manager."""

from __future__ import annotations

import importlib.metadata
from types import MappingProxyType
from typing import Any

import pytest
from mirror_core.exceptions import LifecycleError
from mirror_core.extensions import (
    CapabilityManifest,
    ExtensionKind,
    ExtensionLifecycleManager,
    ExtensionLifecycleState,
    ProviderManifest,
)


class FakeEntryPoint:
    """Simple stand-in for an importlib entry point."""

    def __init__(self, name: str, value: Any) -> None:
        self.name = name
        self._value = value

    def load(self) -> Any:
        return self._value


def _capability_manifest() -> CapabilityManifest:
    return CapabilityManifest(
        extension_id="fetch",
        name="fetch",
        version="1.0.0",
        kind=ExtensionKind.CAPABILITY,
        protocol="mirror_fetch.contracts:FetchProtocol",
        runner="mirror_fetch.runner:run",
    )


def _provider_manifest() -> ProviderManifest:
    return ProviderManifest(
        extension_id="fetch-httpx",
        name="httpx",
        version="1.0.0",
        kind=ExtensionKind.PROVIDER,
        capability="fetch",
        factory="mirror_fetch_httpx.provider:HTTPXProvider",
    )


def test_extension_lifecycle_manager_full_flow(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Discover, validate, configure, activate, deactivate, and unload."""
    capability = _capability_manifest()
    provider = _provider_manifest()

    def mock_entry_points(group: str):
        mapping = {
            "mirror.capabilities": [FakeEntryPoint("fetch", capability)],
            "mirror.providers": [FakeEntryPoint("fetch-httpx", provider)],
        }
        return mapping.get(group, [])

    monkeypatch.setattr(importlib.metadata, "entry_points", mock_entry_points)

    manager = ExtensionLifecycleManager()
    discovered, discovery_errors = manager.discover()
    assert discovery_errors == []
    assert {manifest.extension_id for manifest in discovered} == {
        "fetch",
        "fetch-httpx",
    }
    assert manager.get_record("fetch").state == ExtensionLifecycleState.DISCOVERED
    assert manager.get_record("fetch-httpx").state == ExtensionLifecycleState.DISCOVERED

    valid, validation_errors = manager.validate(discovered)
    assert validation_errors == []
    assert {manifest.extension_id for manifest in valid} == {"fetch", "fetch-httpx"}
    assert manager.get_record("fetch").state == ExtensionLifecycleState.VALIDATED
    assert manager.get_record("fetch-httpx").state == ExtensionLifecycleState.VALIDATED

    manager.configure(valid, configuration={"fetch": {"provider": "httpx"}})
    assert manager.get_record("fetch").state == ExtensionLifecycleState.CONFIGURED
    assert manager.get_record("fetch").configuration == {"provider": "httpx"}

    manager.activate(valid)
    assert manager.registry.get_capability("fetch").extension_id == "fetch"
    assert manager.registry.get_provider("fetch", "httpx").extension_id == "fetch-httpx"
    assert manager.get_record("fetch").state == ExtensionLifecycleState.ACTIVATED
    assert manager.get_record("fetch-httpx").state == ExtensionLifecycleState.ACTIVATED

    manager.deactivate(valid)
    assert manager.get_record("fetch").state == ExtensionLifecycleState.DEACTIVATED
    assert manager.get_record("fetch-httpx").state == ExtensionLifecycleState.DEACTIVATED

    manager.unload(valid)
    assert manager.get_record("fetch").state == ExtensionLifecycleState.UNLOADED
    assert manager.get_record("fetch-httpx").state == ExtensionLifecycleState.UNLOADED


def test_extension_lifecycle_rejects_conflicting_manifests() -> None:
    """Lifecycle manager should reject manifest replacements for one id."""

    manager = ExtensionLifecycleManager()
    capability = _capability_manifest()
    conflicting = CapabilityManifest(
        extension_id="fetch",
        name="Fetch Capability (replacement)",
        version="2.0.0",
        kind=ExtensionKind.CAPABILITY,
        protocol="mirror_fetch.contracts:FetchProtocol",
        runner="mirror_fetch.runner:run",
    )

    manager.discover(groups=[])
    valid, errors = manager.validate([capability])
    assert errors == []
    manager.configure(valid)
    manager.activate(valid)

    with pytest.raises(LifecycleError, match="Conflicting manifest"):
        manager.activate([conflicting])


def test_extension_lifecycle_rejects_out_of_order_transitions() -> None:
    """Lifecycle transitions must stay in Core's explicit order."""
    manager = ExtensionLifecycleManager()
    capability = _capability_manifest()

    with pytest.raises(LifecycleError, match="must be discovered"):
        manager.configure([capability])

    manager.discover(groups=[])
    valid, errors = manager.validate([capability])
    assert errors == []
    with pytest.raises(LifecycleError, match="cannot be activated"):
        manager.activate(valid)

    manager.configure(valid)
    manager.activate(valid)
    with pytest.raises(LifecycleError, match="cannot be unloaded"):
        manager.unload(valid)


def test_extension_lifecycle_configuration_snapshots_are_immutable() -> None:
    """Lifecycle configuration should be captured as a read-only snapshot."""

    manager = ExtensionLifecycleManager()
    capability = _capability_manifest()

    valid, errors = manager.validate([capability])
    assert errors == []

    manager.configure(valid, configuration={"fetch": {"provider": "httpx"}})

    record = manager.get_record("fetch")
    assert isinstance(record.configuration, MappingProxyType)

    with pytest.raises(TypeError):
        record.configuration["provider"] = "other"  # type: ignore[index]
