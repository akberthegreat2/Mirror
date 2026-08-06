"""In-memory Search provider."""

from __future__ import annotations

from mirror_core.registry import ProviderConfig
from mirror_search.models import SearchRequest, SearchResult
from mirror_search.protocol import Search
from mirror_search.settings import SearchSettings

from .index import MemorySearchIndex


class SearchMemoryProvider(Search):
    def __init__(self, settings: SearchSettings | None = None) -> None:
        self._settings = settings or SearchSettings()
        self._index = MemorySearchIndex()

    async def search(self, request: SearchRequest) -> SearchResult:
        limit = min(request.limit, self._settings.default_limit)
        hits = self._index.search(request.query, limit=limit)
        return SearchResult(
            query=request.query,
            hits=hits,
            total=len(hits),
            index_name=self._settings.index_name,
        )


provider = ProviderConfig(
    name="memory",
    capability="search",
    capability_api="~=1.0",
    factory="mirror_search_memory.provider:SearchMemoryProvider",
    settings_model="mirror_search.settings:SearchSettings",
    metadata={"description": "In-memory provider for Mirror Search."},
)
