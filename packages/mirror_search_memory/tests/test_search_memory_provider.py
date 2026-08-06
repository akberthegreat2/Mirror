from mirror_search.models import SearchRequest, SearchResult
from mirror_search_memory import MemorySearchIndex, SearchMemoryProvider


def test_memory_search_index_works() -> None:
    index = MemorySearchIndex()
    index.add("doc-1", text="hello world", title="Hello")
    hits = index.search("hello")
    assert hits and hits[0].document_id == "doc-1"


import pytest


@pytest.mark.asyncio
async def test_search_memory_provider_works() -> None:
    provider = SearchMemoryProvider()
    result = await provider.search(SearchRequest(query="mirror"))
    assert isinstance(result, SearchResult)
    assert result.query == "mirror"
