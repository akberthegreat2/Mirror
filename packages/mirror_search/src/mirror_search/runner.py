"""Search runner – adapts a resolved provider to the capability contract."""

from __future__ import annotations

from .errors import SearchError
from .models import SearchRequest, SearchResult
from .protocol import Search


async def search_step(provider: Search, request: SearchRequest) -> SearchResult:
    try:
        return await provider.search(request)
    except SearchError:
        raise
    except Exception as exc:
        raise SearchError(
            f"Failed to search {request.query}",
            details={"query": request.query},
            cause=exc,
        ) from exc
