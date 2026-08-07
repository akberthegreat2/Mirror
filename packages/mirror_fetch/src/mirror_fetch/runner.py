"""Fetch step runner – adapts pipeline inputs to provider contract."""

from __future__ import annotations

from mirror_core.executor_support import RunnerContext

from mirror_fetch.exceptions import FetchError
from mirror_fetch.models import FetchRequest, FetchResult
from mirror_fetch.protocol import Fetch


async def fetch_step(
    provider: Fetch,
    request: FetchRequest,
    runner_context: RunnerContext | None = None,
) -> FetchResult:
    """Adapt a Fetch provider to the capability runner contract."""
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
