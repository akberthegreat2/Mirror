"""Capability descriptor for Fetch."""

from mirror_core.registry import CapabilityConfig

from mirror_fetch.models import FetchRequest, FetchResult
from mirror_fetch.protocol import Fetch
from mirror_fetch.settings import FetchSettings

capability = CapabilityConfig(
    name="fetch",
    api_version="1.0",
    protocol=Fetch,
    request_model=FetchRequest,
    result_model=FetchResult,
    settings_model=FetchSettings,
    runner="mirror_fetch.runner:fetch_step",
    input_ports={},
    output_ports={"result": FetchResult},
    metadata={
        "description": "Retrieve web resources via HTTP",
        "examples": [
            {"url": "https://example.com", "method": "GET"},
        ],
    },
)
