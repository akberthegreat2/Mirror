"""Tests for registry."""

import pytest
from mirror_core.exceptions import RegistryError
from mirror_core.registry import CapabilityConfig, ProviderConfig, Registry


def test_register_capability():
    r = Registry()
    cap = CapabilityConfig(name="fetch", api_version="1.0")
    r.register_capability(cap)
    assert r.get_capability("fetch", "1.0") is cap


def test_register_provider():
    r = Registry()
    prov = ProviderConfig(name="httpx", capability="fetch", capability_api="~=1.0", factory="a:b")
    r.register_provider(prov)
    assert r.get_provider("fetch", "httpx") is prov


def test_duplicate_capability():
    r = Registry()
    r.register_capability(CapabilityConfig(name="fetch", api_version="1.0"))
    with pytest.raises(RegistryError):
        r.register_capability(CapabilityConfig(name="fetch", api_version="1.0"))


def test_duplicate_provider():
    r = Registry()
    r.register_provider(
        ProviderConfig(name="httpx", capability="fetch", capability_api="~=1.0", factory="a:b")
    )
    with pytest.raises(RegistryError):
        r.register_provider(
            ProviderConfig(name="httpx", capability="fetch", capability_api="~=1.0", factory="a:b")
        )
