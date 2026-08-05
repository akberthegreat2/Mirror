"""Contract tests for WARC provider."""

import pytest

pytest.importorskip("warcio")

from mirror_archive.testing import ArchiveContract
from mirror_archive_warc.provider import WARCProvider


class TestWARCArchiveContract(ArchiveContract):
    provider_class = WARCProvider
