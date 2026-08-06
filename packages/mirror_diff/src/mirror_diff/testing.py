"""Reusable Diff capability test helpers."""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from mirror_core.lifecycle import AsyncLifecycle
from mirror_testing import BaseContract

from mirror_diff.protocol import Diff


class DiffContract(BaseContract):
    __test__ = False
    provider_class: type[Diff] | None = None

    @pytest.fixture
    def provider(self) -> Diff:
        if self.provider_class is None:
            raise RuntimeError("provider_class must be set")
        return self.provider_class()

    @pytest_asyncio.fixture
    async def started_provider(self, provider: Diff) -> AsyncIterator[Diff]:
        if isinstance(provider, AsyncLifecycle):
            await provider.setup()
        try:
            yield provider
        finally:
            if isinstance(provider, AsyncLifecycle):
                await provider.teardown()
