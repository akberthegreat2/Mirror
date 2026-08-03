"""Contract tests for Fetch providers."""

import pytest
from mirror_core.lifecycle import AsyncLifecycle
from mirror_testing import BaseContract  # Changed from CapabilityContract

from mirror_fetch.exceptions import FetchError
from mirror_fetch.models import FetchRequest, FetchResult
from mirror_fetch.protocol import Fetch


class FetchContract(BaseContract):  # Changed from CapabilityContract
    """Contract tests for Fetch providers.

    Subclass this and set provider_class to test your provider.
    """

    __test__ = False  # Prevent pytest from collecting this base class

    provider_class: type[Fetch] | None = None

    @pytest.fixture
    def provider(self) -> Fetch:
        if self.provider_class is None:
            raise NotImplementedError("provider_class must be set")
        return self.provider_class()

    @pytest.mark.asyncio
    async def test_capability_protocol(self, provider: Fetch) -> None:
        assert isinstance(provider, Fetch)

    @pytest.mark.asyncio
    async def test_request_model(self, provider: Fetch) -> None:
        request = FetchRequest(url="https://example.com")
        try:
            await provider.fetch(request)
        except FetchError:
            pass
        except Exception as e:
            pytest.fail(f"Unexpected exception: {e}")

    @pytest.mark.asyncio
    async def test_result_model(self, provider: Fetch) -> None:
        request = FetchRequest(url="https://httpbin.org/get")
        try:
            result = await provider.fetch(request)
            assert isinstance(result, FetchResult)
        except FetchError:
            pytest.skip("Network unavailable")

    @pytest.mark.asyncio
    async def test_error_translation(self, provider: Fetch) -> None:
        request = FetchRequest(url="https://invalid-domain-that-does-not-exist.local")
        with pytest.raises(FetchError):
            await provider.fetch(request)

    @pytest.mark.asyncio
    async def test_lifecycle(self, provider: Fetch) -> None:
        if not isinstance(provider, AsyncLifecycle):
            pytest.skip("Provider does not implement AsyncLifecycle")
        await provider.setup()
        await provider.setup()
        await provider.teardown()
        await provider.teardown()
