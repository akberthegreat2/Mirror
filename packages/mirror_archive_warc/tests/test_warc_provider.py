"""Deterministic tests for the WARC provider."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any, BinaryIO
from uuid import uuid4

import pytest
from mirror_archive.exceptions import ArchiveError
from mirror_archive.models import ArchivePayload, ArchiveRequest
from mirror_archive_warc.provider import WARCProvider
from mirror_archive_warc.settings import WARCSettings


class FakeWARCWriter:
    """Small writer double that records create/write calls."""

    instances: list[FakeWARCWriter] = []

    def __init__(self, stream: BinaryIO, *, gzip: bool) -> None:
        self.stream = stream
        self.gzip = gzip
        self.created: list[dict[str, Any]] = []
        self.written: list[dict[str, Any]] = []
        type(self).instances.append(self)

    def create_warc_record(self, **kwargs: Any) -> dict[str, Any]:
        payload = kwargs["payload"].read()
        record = {**kwargs, "payload_bytes": payload}
        self.created.append(record)
        return record

    def write_record(self, record: dict[str, Any]) -> None:
        self.written.append(record)
        self.stream.write(record["payload_bytes"])


class StubWARCProvider(WARCProvider):
    """Provider wired to a deterministic writer double."""

    @staticmethod
    def _load_writer_class() -> type[FakeWARCWriter]:
        return FakeWARCWriter


def request(content: bytes = b"test content") -> ArchiveRequest:
    return ArchiveRequest(
        resource_id=uuid4(),
        payload=ArchivePayload(
            content=content,
            target_uri="https://example.com/page",
            media_type="text/html",
            headers={"Content-Language": "en"},
        ),
        metadata={"source\r\nInjected": "test\nvalue"},
    )


@pytest.fixture(autouse=True)
def reset_writer_instances() -> None:
    FakeWARCWriter.instances.clear()


@pytest.mark.asyncio
async def test_setup_and_teardown_are_idempotent(tmp_path: Path) -> None:
    provider = StubWARCProvider(WARCSettings(output_dir=tmp_path, compress=False))

    await provider.setup()
    first_writer = provider._writer
    await provider.setup()

    assert provider._writer is first_writer
    assert provider._current_file is not None
    assert provider._current_file.suffix == ".warc"

    await provider.teardown()
    await provider.teardown()
    assert provider._writer is None
    assert provider._current_file is None


@pytest.mark.asyncio
async def test_archive_requires_explicit_setup(tmp_path: Path) -> None:
    provider = StubWARCProvider(WARCSettings(output_dir=tmp_path))

    with pytest.raises(ArchiveError, match="not initialized"):
        await provider.archive(request())


@pytest.mark.asyncio
async def test_archive_creates_resource_record_with_valid_warc_arguments(
    tmp_path: Path,
) -> None:
    provider = StubWARCProvider(WARCSettings(output_dir=tmp_path, compress=False))
    await provider.setup()

    archive_request = request()
    result = await provider.archive(archive_request)
    writer = FakeWARCWriter.instances[-1]
    created = writer.created[-1]

    assert created["uri"] == archive_request.payload.target_uri
    assert created["record_type"] == "resource"
    assert created["payload_bytes"] == archive_request.payload.content
    assert created["length"] == len(archive_request.payload.content)
    assert created["warc_content_type"] == "text/html"
    assert "http_headers" not in created
    assert created["warc_headers_dict"]["WARC-Payload-Digest"].startswith("sha256:")
    assert "Mirror-Metadata-sourceInjected" in created["warc_headers_dict"]
    assert "\n" not in created["warc_headers_dict"]["Mirror-Metadata-sourceInjected"]
    assert result.path.endswith(".warc")
    assert result.size == len(archive_request.payload.content)
    assert result.checksum is not None

    await provider.teardown()


@pytest.mark.asyncio
async def test_rotates_before_writing_record_that_exceeds_segment_limit(
    tmp_path: Path,
) -> None:
    provider = StubWARCProvider(
        WARCSettings(
            output_dir=tmp_path,
            compress=False,
            max_file_bytes=5,
            max_records=100,
        )
    )
    await provider.setup()

    first = await provider.archive(request(b"1234"))
    second = await provider.archive(request(b"5678"))

    assert first.path != second.path
    assert len(FakeWARCWriter.instances) == 2
    await provider.teardown()


@pytest.mark.asyncio
async def test_serializes_concurrent_writes(tmp_path: Path) -> None:
    provider = StubWARCProvider(
        WARCSettings(output_dir=tmp_path, compress=False, max_records=100)
    )
    await provider.setup()

    results = await asyncio.gather(*(provider.archive(request(str(i).encode())) for i in range(20)))

    writer = FakeWARCWriter.instances[-1]
    assert len(writer.written) == 20
    assert len(results) == 20
    assert provider._records == 20
    await provider.teardown()


@pytest.mark.asyncio
async def test_writer_error_is_translated_and_chained(tmp_path: Path) -> None:
    class FailingWriter(FakeWARCWriter):
        def write_record(self, record: dict[str, object]) -> None:
            raise OSError("disk full")

    class FailingProvider(StubWARCProvider):
        @staticmethod
        def _load_writer_class() -> type[FailingWriter]:
            return FailingWriter

    provider = FailingProvider(WARCSettings(output_dir=tmp_path, compress=False))
    await provider.setup()

    with pytest.raises(ArchiveError, match="disk full") as caught:
        await provider.archive(request())

    assert isinstance(caught.value.__cause__, OSError)
    await provider.teardown()
