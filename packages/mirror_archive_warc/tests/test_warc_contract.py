"""Archive capability contract tests for the WARC provider."""

from collections.abc import Iterator
from pathlib import Path
from typing import Any, BinaryIO

import pytest
from mirror_archive.testing import ArchiveContract
from mirror_archive_warc.provider import WARCProvider
from mirror_archive_warc.settings import WARCSettings


class FakeWARCWriter:
    """Minimal deterministic writer used by the reusable contract."""

    def __init__(self, stream: BinaryIO, *, gzip: bool) -> None:
        self.stream = stream
        self.gzip = gzip

    def create_warc_record(self, **kwargs: Any) -> dict[str, Any]:
        payload = kwargs["payload"].read()
        return {**kwargs, "payload_bytes": payload}

    def write_record(self, record: dict[str, Any]) -> None:
        self.stream.write(record["payload_bytes"])


class ContractWARCProvider(WARCProvider):
    """WARC provider with an injected deterministic writer."""

    @staticmethod
    def _load_writer_class() -> type[FakeWARCWriter]:
        return FakeWARCWriter


class TestWARCArchiveContract(ArchiveContract):
    """Run the reusable Archive contract without requiring warcio."""

    __test__ = True
    provider_class = ContractWARCProvider

    @pytest.fixture
    def provider(self, tmp_path: Path) -> Iterator[ContractWARCProvider]:
        yield ContractWARCProvider(WARCSettings(output_dir=tmp_path, compress=False))
