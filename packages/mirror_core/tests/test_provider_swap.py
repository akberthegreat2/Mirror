"""Provider swapping integration tests."""

from __future__ import annotations

import pytest
from mirror_core.application import Application
from mirror_core.extensions.models import MiddlewareManifest, ProviderManifest
from mirror_core.pipeline import Pipeline, Step
from mirror_core.settings import MirrorSettings
from mirror_fetch.capability import capability as fetch_capability
from mirror_fetch.models import FetchRequest, FetchResult
from mirror_fetch_httpx.provider import HTTPXProvider
from mirror_fetch_playwright.provider import PlaywrightProvider


class ProviderSwapDiscoverySource:
    """Discovery source exposing one capability and two providers."""

    def discover(self):
        return [
            fetch_capability,
            ProviderManifest(
                name="httpx",
                capability="fetch",
                capability_api="~=1.0",
                factory="mirror_fetch_httpx.provider:HTTPXProvider",
                settings_model="mirror_fetch_httpx.settings:HTTPXSettings",
                metadata={"version": "1.0.0"},
            ),
            ProviderManifest(
                name="playwright",
                capability="fetch",
                capability_api="~=1.0",
                factory="mirror_fetch_playwright.provider:PlaywrightProvider",
                settings_model="mirror_fetch_playwright.settings:PlaywrightSettings",
                metadata={"version": "1.0.0"},
            ),
            MiddlewareManifest(
                name="retry",
                factory="mirror_core.middleware.builtin.retry:RetryMiddleware",
                settings_model="mirror_core.middleware.builtin.retry:RetrySettings",
                before=["timeout", "ratelimit"],
            ),
        ], []


@pytest.mark.asyncio
async def test_same_pipeline_can_swap_fetch_providers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
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

    async def playwright_fetch(
        self: PlaywrightProvider, request: FetchRequest
    ) -> FetchResult:
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

    async def playwright_setup(self: PlaywrightProvider) -> None:
        self._browser = object()

    async def playwright_teardown(self: PlaywrightProvider) -> None:
        self._browser = None

    monkeypatch.setattr(PlaywrightProvider, "setup", playwright_setup)
    monkeypatch.setattr(PlaywrightProvider, "teardown", playwright_teardown)

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
            result = await app.run_pipeline_detailed(
                pipeline, inputs={"url": "https://example.com"}
            )
        finally:
            await app.shutdown()
        assert result.outcome.value == "succeeded"
        return result.results["fetch_homepage"].payload.content

    assert await run_with("httpx") == b"httpx"
    assert await run_with("playwright") == b"playwright"


@pytest.mark.asyncio
async def test_retry_middleware_is_constructed_through_application(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Application should build retry middleware from its declared settings model."""

    attempts = 0

    async def flaky_httpx_fetch(
        self: HTTPXProvider, request: FetchRequest
    ) -> FetchResult:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise ValueError("temporary network failure")
        return FetchResult(
            url=str(request.url),
            status_code=200,
            headers={"content-type": "text/plain"},
            content=b"retry-ok",
            fetch_duration=0.01,
            timestamp="2026-08-03T00:00:00+00:00",
        )

    monkeypatch.setattr(HTTPXProvider, "fetch", flaky_httpx_fetch)

    pipeline = Pipeline(
        id="retry-fetch",
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

    app = Application(
        MirrorSettings(
            components={"fetch": {"provider": "httpx"}},
            component_settings={"fetch": {"httpx": {}}},
            global_middleware=["retry"],
            middleware={"fetch": []},
            middleware_settings={"retry": {"max_attempts": 2, "base_delay": 0.0}},
            max_concurrency=2,
        ),
        discovery_source=ProviderSwapDiscoverySource(),
    )
    await app.start()
    try:
        result = await app.run_pipeline_detailed(
            pipeline, inputs={"url": "https://example.com"}
        )
    finally:
        await app.shutdown()

    assert result.outcome.value == "succeeded"
    assert result.results["fetch_homepage"].payload.content == b"retry-ok"
    assert attempts == 2
