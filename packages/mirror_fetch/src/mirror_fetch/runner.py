"""Fetch step runner – adapts pipeline inputs to provider contract."""

from __future__ import annotations

from typing import Any

from mirror_fetch.exceptions import FetchError
from mirror_fetch.models import FetchRequest, FetchResult
from mirror_fetch.protocol import Fetch


async def fetch_step(
    provider: Fetch,
    request: FetchRequest,
    settings: Any | None = None,
    signal_bus: Any | None = None,
    step_id: str | None = None,
) -> FetchResult:
    """Adapt a Fetch provider to the capability runner contract."""
    del settings, signal_bus, step_id
    try:
        return await provider.fetch(request)
    except FetchError:
        raise
    except Exception as exc:
        raise FetchError(
            f"Failed to fetch {request.url}: {exc}",
            details={"url": str(request.url)},
            cause=exc,
        ) from exc
