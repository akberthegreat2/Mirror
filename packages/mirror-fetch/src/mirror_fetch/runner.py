"""Fetch step runner – adapts pipeline inputs to provider contract."""

from __future__ import annotations

import logging
from typing import Any

from mirror_fetch.exceptions import FetchError
from mirror_fetch.models import FetchRequest, FetchResult
from mirror_fetch.protocol import Fetch
from mirror_fetch.signals import (
    SIGNAL_FETCH_FAILED,
    SIGNAL_FETCH_STARTED,
    SIGNAL_FETCH_SUCCEEDED,
)

logger = logging.getLogger(__name__)


async def fetch_step(
    provider: Fetch,
    request: FetchRequest,
    settings: Any | None = None,
    signal_bus: Any | None = None,
    step_id: str | None = None,
) -> FetchResult:
    """Run a fetch step.

    Args:
        provider: Fetch provider instance.
        request: FetchRequest with URL and options.
        settings: Optional runtime settings overrides.
        signal_bus: Optional SignalBus for emitting signals.
        step_id: Optional step identifier for signal context.

    Returns:
        FetchResult: The fetched resource.

    Raises:
        FetchError: If the fetch operation fails.
    """
    url = str(request.url)
    logger.debug(f"Fetching: {url}")

    # Emit started signal
    if signal_bus:
        await signal_bus.emit(
            SIGNAL_FETCH_STARTED,
            step_id=step_id,
            url=url,
            request=request,
        )

    try:
        result = await provider.fetch(request)

        # Emit succeeded signal
        if signal_bus:
            await signal_bus.emit(
                SIGNAL_FETCH_SUCCEEDED,
                step_id=step_id,
                url=url,
                result=result,
            )

        return result

    except Exception as e:
        # Emit failed signal
        if signal_bus:
            await signal_bus.emit(
                SIGNAL_FETCH_FAILED,
                step_id=step_id,
                url=url,
                error=str(e),
            )

        raise FetchError(
            f"Failed to fetch {url}: {e}",
            details={"url": url},
            cause=e,
        ) from e
