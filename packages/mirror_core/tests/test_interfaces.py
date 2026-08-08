"""Tests for the interface-neutral manifest projection layer."""

from __future__ import annotations

from typing import Any

from mirror_core.extensions.models import CapabilityManifest, ProviderManifest
from mirror_core.interfaces import InterfaceCatalog


class FakeDiscovery:
    def discover(self) -> tuple[list[Any], list[tuple[str, str]]]:
        return [
            CapabilityManifest(name="fetch", api_version="1.0", runner="module:runner"),
            ProviderManifest(
                name="httpx",
                capability="fetch",
                capability_api="~=1.0",
                factory="module:provider",
            ),
        ], []


def test_interface_catalog_is_framework_neutral() -> None:
    catalog = InterfaceCatalog(source=FakeDiscovery())
    document = catalog.document()
    assert document["capabilities"][0]["name"] == "fetch"
    assert document["providers"][0]["name"] == "httpx"
    assert document["interfaces"] == []
    assert document["errors"] == []
