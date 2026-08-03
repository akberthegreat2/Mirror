"""Tests for HTTPX provider lifecycle."""

import pytest
from mirror_fetch_httpx.provider import HTTPXProvider


@pytest.mark.asyncio
async def test_setup():
    provider = HTTPXProvider()
    assert provider._client is None
    await provider.setup()
    assert provider._client is not None
    await provider.teardown()
    assert provider._client is None


@pytest.mark.asyncio
async def test_setup_idempotent():
    provider = HTTPXProvider()
    await provider.setup()
    client1 = provider._client
    await provider.setup()
    client2 = provider._client
    assert client1 is client2
    await provider.teardown()


@pytest.mark.asyncio
async def test_teardown_idempotent():
    provider = HTTPXProvider()
    await provider.setup()
    await provider.teardown()
    assert provider._client is None
    await provider.teardown()
    assert provider._client is None


@pytest.mark.asyncio
async def test_teardown_safe_on_uninitialized():
    provider = HTTPXProvider()
    await provider.teardown()
    assert provider._client is None
