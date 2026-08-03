"""Tests for lifecycle protocol."""

from mirror_core.lifecycle import AsyncLifecycle


class DummyLifecycle:
    async def setup(self) -> None:
        pass

    async def teardown(self) -> None:
        pass


def test_async_lifecycle_protocol():
    # Just ensure the protocol is defined and a dummy implements it
    assert isinstance(DummyLifecycle(), AsyncLifecycle)
