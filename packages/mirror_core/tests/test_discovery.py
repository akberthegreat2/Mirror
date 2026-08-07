"""Tests for discovery."""

from mirror_core.discovery import DiscoverySource, discover
from mirror_core.extensions.models import CapabilityManifest


class FakeSource(DiscoverySource):
    def __init__(self, entries):
        self._entries = entries

    def discover(self):
        return [obj for _, obj in self._entries], []


def test_discovery_capability():
    fake = FakeSource(
        [
            (
                "fetch",
                CapabilityManifest(
                    name="fetch", api_version="1.0", protocol="module:Protocol"
                ),
            )
        ]
    )
    result = discover(source=fake)
    assert len(result.capabilities) == 1
    assert result.capabilities[0].name == "fetch"


def test_discovery_unknown_type():
    fake = FakeSource([("unknown", {"some": "dict"})])
    result = discover(source=fake)
    assert len(result.errors) == 1
    assert "Unknown manifest type" in result.errors[0][1]


def test_discovery_duplicates():
    fake = FakeSource(
        [
            (
                "fetch1",
                CapabilityManifest(
                    name="fetch", api_version="1.0", protocol="module:Protocol"
                ),
            ),
            (
                "fetch2",
                CapabilityManifest(
                    name="fetch", api_version="1.0", protocol="module:Protocol"
                ),
            ),
        ]
    )
    result = discover(source=fake)
    assert result.has_duplicates()
