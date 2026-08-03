"""Base contract for capability testing.

Capability packages provide a concrete subclass of BaseContract
that defines the test suite for their protocol. Provider packages
run these tests against their implementation.
"""

from typing import Any

import pytest


class BaseContract:
    """Base class for capability contract tests.

    Subclass this and implement the abstract methods to define
    the test suite for a capability.
    """

    provider_class: type[Any] | None = None

    @pytest.fixture
    def provider(self) -> Any:
        """Return an instance of the provider under test."""
        if self.provider_class is None:
            raise NotImplementedError("provider_class must be set")
        return self.provider_class()

    @pytest.mark.asyncio
    async def test_lifecycle(self, provider: Any) -> None:
        """Test that the provider implements AsyncLifecycle correctly."""
        from mirror_core.lifecycle import AsyncLifecycle

        if isinstance(provider, AsyncLifecycle):
            await provider.setup()
            await provider.setup()  # idempotent
            await provider.teardown()
            await provider.teardown()  # idempotent

    @pytest.mark.asyncio
    async def test_capability_protocol(self, provider: Any) -> None:
        """Test that the provider implements the capability protocol."""
        pytest.skip("Subclass must implement this test")

    @pytest.mark.asyncio
    async def test_request_model(self, provider: Any) -> None:
        """Test that the provider accepts the capability's request model."""
        pytest.skip("Subclass must implement this test")

    @pytest.mark.asyncio
    async def test_result_model(self, provider: Any) -> None:
        """Test that the provider returns the capability's result model."""
        pytest.skip("Subclass must implement this test")

    @pytest.mark.asyncio
    async def test_error_translation(self, provider: Any) -> None:
        """Test that provider errors are wrapped in capability-specific errors."""
        pytest.skip("Subclass must implement this test")

    @pytest.mark.asyncio
    async def test_cancellation(self, provider: Any) -> None:
        """Test that the provider handles cancellation."""
        pytest.skip("Subclass must implement this test")

    @pytest.mark.asyncio
    async def test_timeout(self, provider: Any) -> None:
        """Test that the provider respects timeouts."""
        pytest.skip("Subclass must implement this test")
