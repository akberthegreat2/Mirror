"""Tests for the search capability package."""

from __future__ import annotations

import pytest
from mirror_search import SearchRequest, SearchResult, capability, search_step
from mirror_search_memory import MemorySearchIndex, SearchMemoryProvider


class FakeSearchProvider:
    async def search(self, request: SearchRequest) -> SearchResult:
        return SearchResult(query=request.query, hits=[], total=0)


def test_capability_descriptor() -> None:
    assert capability.name == "search"
    assert capability.request_model == SearchRequest
    assert capability.result_model == SearchResult
    assert capability.runner == "mirror_search.runner:search_step"


def test_memory_search_index() -> None:
    index = MemorySearchIndex()
    index.add("doc-1", text="hello world", title="Hello")
    hits = index.search("hello", limit=5)
    assert hits and hits[0].document_id == "doc-1"


@pytest.mark.asyncio
async def test_search_step() -> None:
    result = await search_step(FakeSearchProvider(), SearchRequest(query="hello"))
    assert result.total == 0


@pytest.mark.asyncio
async def test_search_memory_provider() -> None:
    provider = SearchMemoryProvider()
    result = await provider.search(SearchRequest(query="mirror"))
    assert isinstance(result, SearchResult)
