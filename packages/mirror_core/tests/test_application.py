"""Tests for transactional and restartable application lifecycle."""

import sys
from typing import ClassVar, Protocol, runtime_checkable

import pytest
from mirror_core.application import Application
from mirror_core.discovery import DiscoverySource
from mirror_core.registry import CapabilityConfig, ProviderConfig
from mirror_core.settings import MirrorSettings
from pydantic import BaseModel


class ProviderSettings(BaseModel):
    fail_setup: bool = False


@runtime_checkable
class CapabilityProtocol(Protocol):
    async def perform(self) -> None: ...


class Provider:
    instances: ClassVar[list["Provider"]] = []

    def __init__(self, settings: ProviderSettings) -> None:
        self.settings = settings
        self.setup_calls = 0
        self.teardown_calls = 0
        self.__class__.instances.append(self)

    async def setup(self) -> None:
        self.setup_calls += 1
        if self.settings.fail_setup:
            raise RuntimeError("setup failed")

    async def teardown(self) -> None:
        self.teardown_calls += 1

    async def perform(self) -> None:
        return None


sys.modules["mirror_test_provider"] = sys.modules[__name__]


class FakeSource(DiscoverySource):
    def iter_entry_points(self, group: str):
        return [
            (
                "capability",
                lambda: CapabilityConfig(
                    name="example",
                    api_version="1.0",
                    protocol=CapabilityProtocol,
                ),
            ),
            (
                "provider",
                lambda: ProviderConfig(
                    name="default",
                    capability="example",
                    capability_api="~=1.0",
                    factory="mirror_test_provider:Provider",
                    settings_model=ProviderSettings,
                ),
            ),
        ]


@pytest.mark.asyncio
async def test_startup_rolls_back_partially_initialized_provider() -> None:
    Provider.instances.clear()
    app = Application(
        MirrorSettings(
            components={"example": {"provider": "default"}},
            component_settings={"example": {"default": {"fail_setup": True}}},
        ),
        discovery_source=FakeSource(),
    )

    with pytest.raises(RuntimeError, match="setup failed"):
        await app.start()

    instance = Provider.instances[-1]
    assert instance.setup_calls == 1
    assert instance.teardown_calls == 1
    assert app.started is False


@pytest.mark.asyncio
async def test_application_can_restart_cleanly() -> None:
    Provider.instances.clear()
    app = Application(
        MirrorSettings(components={"example": {"provider": "default"}}),
        discovery_source=FakeSource(),
    )

    await app.start()
    first = Provider.instances[-1]
    await app.shutdown()
    await app.start()
    second = Provider.instances[-1]
    await app.shutdown()

    assert first is not second
    assert first.teardown_calls == 1
    assert second.teardown_calls == 1
