"""Playwright-style provider for Mirror Fetch."""

from mirror_core.registry import ProviderConfig

from mirror_fetch_playwright.provider import PlaywrightProvider
from mirror_fetch_playwright.settings import PlaywrightSettings

provider = ProviderConfig(
    name="playwright",
    capability="fetch",
    capability_api="~=1.0",
    factory="mirror_fetch_playwright.provider:PlaywrightProvider",
    settings_model="mirror_fetch_playwright.settings:PlaywrightSettings",
    features=["browser", "javascript", "rendering", "dom"],
    priority=90,
    metadata={
        "description": "Playwright-style fetch provider with a lightweight fallback backend",
        "requires_network": True,
    },
)

__all__ = ["PlaywrightProvider", "PlaywrightSettings", "provider"]
