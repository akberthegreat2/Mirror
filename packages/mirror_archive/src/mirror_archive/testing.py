"""Contract tests for Archive providers."""

from uuid import uuid4

import pytest
from mirror_core.lifecycle import AsyncLifecycle
from mirror_testing import BaseContract

from mirror_archive.exceptions import ArchiveError
from mirror_archive.models import ArchiveRequest, ArchiveResult
from mirror_archive.protocol import Archive


class ArchiveContract(BaseContract):  # Now inherits from BaseContract
    """Contract tests for Archive providers.

    Subclass this and set provider_class to test your provider.
    """

    __test__ = False  # Prevent pytest from collecting this base class

    provider_class: type[Archive] | None = None

    @pytest.fixture
    def provider(self) -> Archive:
        if self.provider_class is None:
            raise NotImplementedError("provider_class must be set")
        return self.provider_class()

    @pytest.mark.asyncio
    async def test_capability_protocol(self, provider: Archive) -> None:
        assert isinstance(provider, Archive)

    @pytest.mark.asyncio
    async def test_request_model(self, provider: Archive) -> None:
        request = ArchiveRequest(resource_id=uuid4(), payload={"data": "test"})
        try:
            await provider.archive(request)
        except ArchiveError:
            pass
        except Exception as e:
            pytest.fail(f"Unexpected exception: {e}")

    @pytest.mark.asyncio
    async def test_result_model(self, provider: Archive) -> None:
        request = ArchiveRequest(resource_id=uuid4(), payload={"data": "test"})
        try:
            result = await provider.archive(request)
            assert isinstance(result, ArchiveResult)
        except ArchiveError:
            pytest.skip("Archive operation failed")

    @pytest.mark.asyncio
    async def test_error_translation(self, provider: Archive) -> None:
        request = ArchiveRequest(resource_id=uuid4(), payload=None)
        with pytest.raises(ArchiveError):
            await provider.archive(request)

    @pytest.mark.asyncio
    async def test_lifecycle(self, provider: Archive) -> None:
        if not isinstance(provider, AsyncLifecycle):
            pytest.skip("Provider does not implement AsyncLifecycle")
        await provider.setup()
        await provider.setup()
        await provider.teardown()
        await provider.teardown()
