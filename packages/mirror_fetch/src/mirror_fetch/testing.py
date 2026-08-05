"""Reusable contract tests for Fetch providers."""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from mirror_core.lifecycle import AsyncLifecycle
from mirror_testing import BaseContract

from mirror_fetch.protocol import Fetch


class FetchContract(BaseContract):
    """Provider-independent structural contract for Fetch implementations.

    Network success and transport-error behavior require provider-specific
    deterministic transports and therefore remain in each provider package's
    tests. This shared suite verifies the common protocol and lifecycle without
    making external internet requests.
    """

    __test__ = False
    provider_class: type[Fetch] | None = None

    @pytest.fixture
    def provider(self) -> Fetch:
        if self.provider_class is None:
            raise RuntimeError("provider_class must be set")
        return self.provider_class()

    @pytest_asyncio.fixture
    async def started_provider(self, provider: Fetch) -> AsyncIterator[Fetch]:
        if isinstance(provider, AsyncLifecycle):
            await provider.setup()
        try:
            yield provider
        finally:
            if isinstance(provider, AsyncLifecycle):
                await provider.teardown()

    def test_capability_protocol(self, provider: Fetch) -> None:
        assert isinstance(provider, Fetch)

    @pytest.mark.asyncio
    async def test_lifecycle_is_idempotent(self, provider: Fetch) -> None:
        if not isinstance(provider, AsyncLifecycle):
            pytest.fail("Fetch providers must implement AsyncLifecycle")
        await provider.setup()
        await provider.setup()
        await provider.teardown()
        await provider.teardown()
