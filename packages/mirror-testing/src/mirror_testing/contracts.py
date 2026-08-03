"""Base classes and utilities for provider contract testing.

Each capability package provides a contract test suite that providers
must pass. This module provides the base infrastructure.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Any, Protocol, TypeVar, runtime_checkable

import pytest
from mirror_core.lifecycle import AsyncLifecycle
from mirror_core.resource import ResourceEnvelope

T = TypeVar("T", bound=AsyncLifecycle)


@runtime_checkable
class CapabilityContract(Protocol):
    """Protocol for capability contract test suites.

    A capability package provides a concrete class that implements
    this protocol. Provider packages then run the contract suite
    against their implementation.
    """

    @staticmethod
    def create_provider(settings: dict[str, Any] | None = None) -> AsyncLifecycle:
        """Create a provider instance for testing."""
        ...

    @staticmethod
    def valid_request() -> Any:
        """Return a valid request for the capability."""
        ...

    @staticmethod
    def invalid_request() -> Any:
        """Return an invalid request (should raise validation error)."""
        ...


class ContractTestCase:
    """Base test case for provider contracts.

    Subclass this and implement the methods to test your provider.
    """

    capability_contract: CapabilityContract

    @pytest.fixture  # type: ignore[misc]
    async def provider(self) -> AsyncGenerator[AsyncLifecycle, None]:
        """Fixture that creates and sets up a provider instance."""
        provider = self.capability_contract.create_provider()
        if isinstance(provider, AsyncLifecycle):
            await provider.setup()
        yield provider
        if isinstance(provider, AsyncLifecycle):
            await provider.teardown()

    @pytest.mark.asyncio  # type: ignore[misc]
    async def test_lifecycle(self, provider: AsyncLifecycle) -> None:
        """Test that the provider implements lifecycle correctly.

        - setup() is idempotent
        - teardown() is idempotent
        - teardown() can be called without setup()
        """
        # setup twice should be safe
        await provider.setup()
        await provider.setup()

        # teardown twice should be safe
        await provider.teardown()
        await provider.teardown()

        # teardown without setup should be safe
        new_provider = self.capability_contract.create_provider()
        await new_provider.teardown()

    @pytest.mark.asyncio  # type: ignore[misc]
    async def test_contract(self, provider: AsyncLifecycle) -> None:
        """Main contract test: provider must handle valid requests and return resources."""
        request = self.capability_contract.valid_request()

        # Provider must have a "process" method that returns ResourceEnvelope
        if not hasattr(provider, "process"):
            pytest.skip("Provider does not implement process()")

        result = await provider.process(request)  # type: ignore

        # Validate result is a ResourceEnvelope
        assert isinstance(result, ResourceEnvelope)
        # TODO: Add more validation based on capability expectations

    @pytest.mark.asyncio  # type: ignore[misc]
    async def test_invalid_request(self, provider: AsyncLifecycle) -> None:
        """Provider must raise an error for invalid requests."""
        request = self.capability_contract.invalid_request()

        if not hasattr(provider, "process"):
            pytest.skip("Provider does not implement process()")

        with pytest.raises(Exception):  # noqa: B017
            await provider.process(request)  # type: ignore


# Helper functions for use in provider packages


def create_provider(
    contract: CapabilityContract,
    settings: dict[str, Any] | None = None,
) -> AsyncLifecycle:
    """Create a provider instance from the contract."""
    return contract.create_provider(settings)


def assert_resource_envelope(
    envelope: ResourceEnvelope,
    expected_type: str | None = None,
    expected_version: str | None = None,
) -> None:
    """Assert that an envelope is valid."""
    assert isinstance(envelope, ResourceEnvelope)
    if expected_type:
        assert envelope.resource_type == expected_type
    if expected_version:
        assert envelope.schema_version == expected_version


def assert_roundtrip(
    original: ResourceEnvelope,
    serialized: dict[str, Any],
) -> None:
    """Assert that a resource survives serialization roundtrip."""
    from pydantic import ValidationError

    try:
        roundtrip = ResourceEnvelope.model_validate(serialized)
    except ValidationError as e:
        raise AssertionError(f"Roundtrip failed: {e}") from e

    assert roundtrip.resource_id == original.resource_id
    assert roundtrip.resource_type == original.resource_type
    assert roundtrip.fingerprint == original.fingerprint
