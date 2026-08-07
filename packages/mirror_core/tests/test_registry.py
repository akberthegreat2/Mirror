"""Tests for registry."""

import pytest
from mirror_core.exceptions import RegistryError
from mirror_core.extensions.models import CapabilityManifest, ProviderManifest
from mirror_core.extensions.registry import ExtensionRegistryManager


def test_register_capability():
    r = ExtensionRegistryManager()
    cap = CapabilityManifest(
        name="fetch", api_version="1.0", protocol="module:Protocol"
    )
    r.register_capability(cap)
    assert r.get_capability("fetch", "1.0") is cap


def test_register_provider():
    r = ExtensionRegistryManager()
    prov = ProviderManifest(
        name="httpx", capability="fetch", capability_api="~=1.0", factory="a:b"
    )
    r.register_provider(prov)
    assert r.get_provider("fetch", "httpx") is prov


def test_duplicate_capability():
    r = ExtensionRegistryManager()
    r.register_capability(
        CapabilityManifest(name="fetch", api_version="1.0", protocol="module:Protocol")
    )
    with pytest.raises(RegistryError):
        r.register_capability(
            CapabilityManifest(
                name="fetch", api_version="1.0", protocol="module:Protocol"
            )
        )


def test_duplicate_provider():
    r = ExtensionRegistryManager()
    r.register_provider(
        ProviderManifest(
            name="httpx", capability="fetch", capability_api="~=1.0", factory="a:b"
        )
    )
    with pytest.raises(RegistryError):
        r.register_provider(
            ProviderManifest(
                name="httpx", capability="fetch", capability_api="~=1.0", factory="a:b"
            )
        )
