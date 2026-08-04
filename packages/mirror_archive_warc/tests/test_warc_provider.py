"""Tests for WARC provider."""

import pytest

pytest.importorskip("warcio")

from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4

from mirror_archive.models import ArchivePayload, ArchiveRequest
from mirror_archive_warc.provider import WARCProvider
from mirror_archive_warc.settings import WARCSettings


@pytest.mark.asyncio
async def test_provider_setup():
    with TemporaryDirectory() as tmpdir:
        settings = WARCSettings(output_dir=Path(tmpdir))
        provider = WARCProvider(settings=settings)
        await provider.setup()
        assert provider._writer is not None
        assert provider._current_file is not None
        await provider.teardown()


@pytest.mark.asyncio
async def test_provider_archive():
    with TemporaryDirectory() as tmpdir:
        settings = WARCSettings(output_dir=Path(tmpdir))
        provider = WARCProvider(settings=settings)
        await provider.setup()

        request = ArchiveRequest(
            resource_id=uuid4(),
            payload=ArchivePayload(content=b"test content", target_uri="https://example.com"),
            metadata={"source": "test"},
        )

        result = await provider.archive(request)
        assert result.size > 0
        assert result.path.endswith(".warc") or result.path.endswith(".warc.gz")
        assert result.checksum is not None

        await provider.teardown()


@pytest.mark.asyncio
async def test_provider_no_setup_auto():
    with TemporaryDirectory() as tmpdir:
        settings = WARCSettings(output_dir=Path(tmpdir))
        provider = WARCProvider(settings=settings)

        request = ArchiveRequest(resource_id=uuid4(), payload=ArchivePayload(content=b"test"))
        with pytest.raises(Exception, match="not initialized"):
            await provider.archive(request)
