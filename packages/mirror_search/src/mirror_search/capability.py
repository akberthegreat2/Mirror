"""Capability descriptor for Search."""

from mirror_core.extensions.models import CapabilityManifest

from .models import SearchRequest, SearchResult
from .protocol import Search
from .settings import SearchSettings

capability = CapabilityManifest(
    name="search",
    api_version="1.0.0",
    protocol=Search,
    request_model=SearchRequest,
    result_model=SearchResult,
    settings_model=SearchSettings,
    runner="mirror_search.runner:search_step",
    metadata={"summary": "Search capability"},
)
