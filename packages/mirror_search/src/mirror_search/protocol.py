"""Search capability protocol."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from .models import SearchRequest, SearchResult


@runtime_checkable
class Search(Protocol):
    """Protocol for search providers."""

    async def search(self, request: SearchRequest) -> SearchResult: ...
