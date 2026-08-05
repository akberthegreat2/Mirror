"""Contract tests for HTTPX provider against FetchContract."""

from mirror_fetch.testing import FetchContract
from mirror_fetch_httpx.provider import HTTPXProvider


class TestHTTPXFetchContract(FetchContract):
    __test__ = True
    provider_class = HTTPXProvider
