"""Contract tests for HTTPX provider against FetchContract."""

from mirror_fetch.testing import FetchContract
from mirror_fetch_httpx.provider import HTTPXProvider


class TestHTTPXFetchContract(FetchContract):
    provider_class = HTTPXProvider
