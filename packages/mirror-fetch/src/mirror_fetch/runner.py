"""Fetch step runner – adapts pipeline inputs to provider contract."""

from __future__ import annotations

import logging
from typing import Any

from mirror_fetch.exceptions import FetchError
from mirror_fetch.models import FetchRequest, FetchResult
from mirror_fetch.protocol import Fetch

logger = logging.getLogger(__name__)


async def fetch_step(
    provider: Fetch, request: FetchRequest, settings: Any | None = None
) -> FetchResult:
    """Run a fetch step.

    Args:
        provider: Fetch provider instance.
        request: FetchRequest with URL and options.
        settings: Optional runtime settings overrides (currently unused).

    Returns:
        FetchResult: The fetched resource.

    Raises:
        FetchError: If the fetch operation fails.
    """
    logger.debug(f"Fetching: {request.url}")

    try:
        result = await provider.fetch(request)
        return result
    except Exception as e:
        raise FetchError(
            f"Failed to fetch {request.url}: {e}",
            details={"url": str(request.url)},
            cause=e,
        ) from e
