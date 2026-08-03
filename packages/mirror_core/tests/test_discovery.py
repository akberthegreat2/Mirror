"""Tests for discovery."""

from mirror_core.discovery import DiscoverySource, discover
from mirror_core.registry import CapabilityConfig


class FakeSource(DiscoverySource):
    def __init__(self, entries):
        self._entries = entries

    def iter_entry_points(self, group: str):
        return [(name, lambda obj=obj: obj) for name, obj in self._entries]


def test_discovery_capability():
    fake = FakeSource([("fetch", CapabilityConfig(name="fetch", api_version="1.0"))])
    result = discover(source=fake)
    assert len(result.capabilities) == 1
    assert result.capabilities[0].name == "fetch"


def test_discovery_unknown_type():
    fake = FakeSource([("unknown", {"some": "dict"})])
    result = discover(source=fake)
    assert len(result.errors) == 1
    assert "Unknown descriptor type" in result.errors[0][1]


def test_discovery_duplicates():
    fake = FakeSource(
        [
            ("fetch1", CapabilityConfig(name="fetch", api_version="1.0")),
            ("fetch2", CapabilityConfig(name="fetch", api_version="1.0")),
        ]
    )
    result = discover(source=fake)
    assert result.has_duplicates()
