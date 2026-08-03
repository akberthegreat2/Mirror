"""Fetch capability protocol."""

from typing import Protocol, runtime_checkable

from mirror_fetch.models import FetchRequest, FetchResult


@runtime_checkable
class Fetch(Protocol):
    """Protocol for fetch providers.

    Implementations handle HTTP requests, including headers, timeouts,
    retries, and browser automation.
    """

    async def fetch(self, request: FetchRequest) -> FetchResult:
        """Fetch a URL and return the resource.

        Args:
            request: Typed fetch request with URL and options.

        Returns:
            FetchResult: The fetched resource.

        Raises:
            FetchError: If the request fails after retries.
        """
        ...
