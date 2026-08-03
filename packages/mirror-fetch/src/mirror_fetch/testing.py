"""Contract tests for Fetch providers."""

from typing import Any, cast

import pytest
from mirror_testing.contracts import CapabilityContract

from mirror_fetch.exceptions import FetchError
from mirror_fetch.models import FetchRequest, FetchResult
from mirror_fetch.protocol import Fetch


class FetchContract(CapabilityContract):
    """Contract tests for Fetch providers.

    Subclass this and set provider_class to test your provider.
    """

    provider_class: type[Fetch] | None = None

    @pytest.fixture
    def provider(self) -> Fetch:
        if self.provider_class is None:
            raise NotImplementedError("provider_class must be set")
        return self.provider_class()

    @pytest.mark.asyncio
    async def test_capability_protocol(self, provider: Fetch) -> None:
        """Test that provider implements Fetch protocol."""
        assert isinstance(provider, Fetch)

    @pytest.mark.asyncio
    async def test_request_model(self, provider: Fetch) -> None:
        """Test that provider accepts a FetchRequest."""
        request = FetchRequest(url="https://example.com")
        try:
            await provider.fetch(request)
        except FetchError:
            pass
        except Exception as e:
            pytest.fail(f"Unexpected exception: {e}")

    @pytest.mark.asyncio
    async def test_result_model(self, provider: Fetch) -> None:
        """Test that provider returns a FetchResult."""
        request = FetchRequest(url="https://httpbin.org/get")
        try:
            result = await provider.fetch(request)
            assert isinstance(result, FetchResult)
        except FetchError:
            pytest.skip("Network unavailable")

    @pytest.mark.asyncio
    async def test_error_translation(self, provider: Fetch) -> None:
        """Test that provider errors are wrapped in FetchError."""
        request = FetchRequest(url="https://invalid-domain-that-does-not-exist.local")
        with pytest.raises(FetchError):
            await provider.fetch(request)

    @pytest.mark.asyncio
    async def test_lifecycle(self, provider: Fetch) -> None:
        """Test AsyncLifecycle if implemented."""
        if not hasattr(provider, "setup"):
            pytest.skip("Provider does not implement AsyncLifecycle")
        # Cast to Any for lifecycle calls
        lifecycle = cast(Any, provider)
        await lifecycle.setup()
        await lifecycle.setup()
        await lifecycle.teardown()
        await lifecycle.teardown()
