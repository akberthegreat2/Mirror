"""Reusable Search capability test helpers."""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from mirror_core.lifecycle import AsyncLifecycle
from mirror_testing import BaseContract

from mirror_search.protocol import Search


class SearchContract(BaseContract):
    """Reusable contract tests for Search providers."""

    __test__ = False
    provider_class: type[Search] | None = None

    @pytest.fixture
    def provider(self) -> Search:
        if self.provider_class is None:
            raise RuntimeError("provider_class must be set")
        return self.provider_class()

    @pytest_asyncio.fixture
    async def started_provider(self, provider: Search) -> AsyncIterator[Search]:
        if isinstance(provider, AsyncLifecycle):
            await provider.setup()
        try:
            yield provider
        finally:
            if isinstance(provider, AsyncLifecycle):
                await provider.teardown()
