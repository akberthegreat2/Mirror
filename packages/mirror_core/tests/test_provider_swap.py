"""Provider swapping integration tests."""

from __future__ import annotations

import pytest

from mirror_core.application import Application
from mirror_core.pipeline import Pipeline, Step
from mirror_core.registry import ProviderConfig
from mirror_core.settings import MirrorSettings
from mirror_fetch.capability import capability as fetch_capability
from mirror_fetch.models import FetchRequest, FetchResult
from mirror_fetch_httpx.provider import HTTPXProvider
from mirror_fetch_playwright.provider import PlaywrightProvider


class ProviderSwapDiscoverySource:
    """Discovery source exposing one capability and two providers."""

    def iter_entry_points(self, group: str):
        assert group == "mirror"
        return [
            ("fetch", lambda: fetch_capability),
            (
                "fetch-httpx",
                lambda: ProviderConfig(
                    name="httpx",
                    capability="fetch",
                    capability_api="~=1.0",
                    factory="mirror_fetch_httpx.provider:HTTPXProvider",
                    settings_model="mirror_fetch_httpx.settings:HTTPXSettings",
                    metadata={"version": "1.0.0"},
                ),
            ),
            (
                "fetch-playwright",
                lambda: ProviderConfig(
                    name="playwright",
                    capability="fetch",
                    capability_api="~=1.0",
                    factory="mirror_fetch_playwright.provider:PlaywrightProvider",
                    settings_model="mirror_fetch_playwright.settings:PlaywrightSettings",
                    metadata={"version": "1.0.0"},
                ),
            ),
        ]


@pytest.mark.asyncio
async def test_same_pipeline_can_swap_fetch_providers(monkeypatch: pytest.MonkeyPatch) -> None:
    """The same pipeline should run against different fetch providers."""

    async def httpx_fetch(self: HTTPXProvider, request: FetchRequest) -> FetchResult:
        return FetchResult(
            url=str(request.url),
            status_code=200,
            headers={"content-type": "text/plain"},
            content=b"httpx",
            fetch_duration=0.01,
            timestamp="2026-08-03T00:00:00+00:00",
        )

    async def playwright_fetch(self: PlaywrightProvider, request: FetchRequest) -> FetchResult:
        return FetchResult(
            url=str(request.url),
            status_code=200,
            headers={"content-type": "text/plain"},
            content=b"playwright",
            fetch_duration=0.01,
            timestamp="2026-08-03T00:00:00+00:00",
        )

    monkeypatch.setattr(HTTPXProvider, "fetch", httpx_fetch)
    monkeypatch.setattr(PlaywrightProvider, "fetch", playwright_fetch)

    pipeline = Pipeline(
        id="swap-fetch",
        inputs={"url": "str"},
        steps=[
            Step(
                id="fetch_homepage",
                capability="fetch",
                input={"url": "$pipeline.url"},
                outputs=["result"],
            )
        ],
    )

    async def run_with(provider_name: str) -> bytes:
        app = Application(
            MirrorSettings(
                components={"fetch": {"provider": provider_name}},
                component_settings={"fetch": {provider_name: {}}},
                global_middleware=[],
                middleware={},
                middleware_settings={},
                max_concurrency=2,
            ),
            discovery_source=ProviderSwapDiscoverySource(),
        )
        await app.start()
        try:
            result = await app.run_pipeline_detailed(pipeline, inputs={"url": "https://example.com"})
        finally:
            await app.shutdown()
        assert result.outcome.value == "succeeded"
        return result.results["fetch_homepage"].payload.content

    assert await run_with("httpx") == b"httpx"
    assert await run_with("playwright") == b"playwright"
