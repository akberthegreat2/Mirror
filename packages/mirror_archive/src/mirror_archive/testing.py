"""Reusable contract tests for Archive providers."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import cast
from uuid import uuid4

import pytest
import pytest_asyncio
from mirror_core.lifecycle import AsyncLifecycle
from mirror_testing import BaseContract

from mirror_archive.exceptions import ArchiveError
from mirror_archive.models import ArchivePayload, ArchiveRequest, ArchiveResult
from mirror_archive.protocol import Archive


class ArchiveContract(BaseContract):
    """Provider-independent structural contract for Archive implementations."""

    __test__ = False
    provider_class: type[Archive] | None = None

    @pytest.fixture
    def provider(self) -> Archive:
        if self.provider_class is None:
            raise RuntimeError("provider_class must be set")
        return self.provider_class()

    @pytest_asyncio.fixture
    async def started_provider(self, provider: Archive) -> AsyncIterator[Archive]:
        if isinstance(provider, AsyncLifecycle):
            await provider.setup()
        try:
            yield provider
        finally:
            if isinstance(provider, AsyncLifecycle):
                await provider.teardown()

    def valid_request(self) -> ArchiveRequest:
        """Build a deterministic request for contract tests."""
        return ArchiveRequest(
            resource_id=uuid4(),
            payload=ArchivePayload(
                content=b"mirror archive contract",
                target_uri="https://example.com/contract",
                media_type="text/plain",
            ),
            metadata={"contract": "archive"},
        )

    def test_capability_protocol(self, provider: Archive) -> None:
        """Verify that the provider satisfies the Archive protocol."""
        assert isinstance(provider, Archive)

    @pytest.mark.asyncio
    async def test_result_model(self, started_provider: Archive) -> None:
        """Verify that successful calls return the published result model."""
        result = await started_provider.archive(self.valid_request())
        assert isinstance(result, ArchiveResult)
        assert result.size == len(b"mirror archive contract")
        assert result.checksum is not None

    @pytest.mark.asyncio
    async def test_invalid_request_is_translated(self, started_provider: Archive) -> None:
        """Verify that providers reject malformed payloads through their contract."""
        invalid = ArchiveRequest.model_construct(resource_id=uuid4(), payload=cast(ArchivePayload, None))
        with pytest.raises(ArchiveError):
            await started_provider.archive(invalid)

    @pytest.mark.asyncio
    async def test_lifecycle_is_idempotent(self, provider: Archive) -> None:
        """Verify setup/teardown can safely be called more than once."""
        if not isinstance(provider, AsyncLifecycle):
            pytest.skip("Provider does not implement AsyncLifecycle")
        await provider.setup()
        await provider.setup()
        await provider.teardown()
        await provider.teardown()
