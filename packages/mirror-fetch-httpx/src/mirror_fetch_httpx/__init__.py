"""HTTPX provider for Mirror Fetch capability."""

from mirror_fetch_httpx.provider import HTTPXProvider
from mirror_fetch_httpx.settings import HTTPXSettings

# Provider descriptor for discovery
provider = {
    "name": "httpx",
    "capability": "fetch",
    "capability_api": "~=1.0",
    "factory": "mirror_fetch_httpx.provider:HTTPXProvider",
    "settings_model": "mirror_fetch_httpx.settings:HTTPXSettings",
    "features": ["http", "https", "http2", "redirects", "streaming"],
    "priority": 100,
    "metadata": {
        "description": "HTTPX-based fetch provider",
        "requires_network": True,
    },
}

__all__ = ["HTTPXProvider", "HTTPXSettings", "provider"]
