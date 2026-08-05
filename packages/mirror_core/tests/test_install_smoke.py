"""Install and import smoke tests for real-world package usage."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[3]
PACKAGE_PATHS = [
    ROOT / "packages" / "mirror_core",
    ROOT / "packages" / "mirror_fetch",
    ROOT / "packages" / "mirror_fetch_httpx",
    ROOT / "packages" / "mirror_fetch_playwright",
    ROOT / "packages" / "mirror_middleware",
    ROOT / "packages" / "mirror_testing",
]


def _bootstrap_source_paths() -> None:
    """Make the workspace packages importable from a source checkout."""

    for src in sorted((ROOT / "packages").glob("*/src")):
        path = str(src)
        if path not in sys.path:
            sys.path.insert(0, path)


def test_local_install_and_import_smoke(tmp_path: Path) -> None:
    """Install the core stack into an isolated target and import it back."""

    target = tmp_path / "site-packages"
    target.mkdir()

    install = [
        sys.executable,
        "-m",
        "pip",
        "install",
        "--no-deps",
        "--no-build-isolation",
        "--target",
        str(target),
        *(str(path) for path in PACKAGE_PATHS),
    ]
    subprocess.run(install, check=True, capture_output=True, text=True)

    probe = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import mirror_core, mirror_fetch, mirror_fetch_httpx, "
                "mirror_fetch_playwright, mirror_middleware, mirror_testing; "
                "from mirror_fetch import capability; "
                "from mirror_fetch_httpx import provider as httpx_provider; "
                "from mirror_fetch_playwright import provider as playwright_provider; "
                "print(capability.name, httpx_provider.name, playwright_provider.name)"
            ),
        ],
        check=True,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": str(target)},
    )

    assert probe.stdout.strip() == "fetch httpx playwright"


@pytest.mark.asyncio
async def test_real_world_fetch_pipeline_uses_actual_packages(monkeypatch: pytest.MonkeyPatch) -> None:
    """Run a representative Fetch pipeline using the real core and provider packages."""

    _bootstrap_source_paths()

    from mirror_core.application import Application
    from mirror_core.pipeline import Pipeline, Step
    from mirror_core.registry import CapabilityConfig, ProviderConfig
    from mirror_core.settings import MirrorSettings
    from mirror_fetch.capability import capability as fetch_capability
    from mirror_fetch.models import FetchRequest, FetchResult
    from mirror_fetch.protocol import Fetch
    from mirror_fetch_httpx.provider import HTTPXProvider
    from mirror_fetch_playwright.provider import PlaywrightProvider

    class RealDiscoverySource:
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
        id="smoke-fetch",
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

    async def run_with_provider(provider_name: str) -> bytes:
        app = Application(
            MirrorSettings(
                components={"fetch": {"provider": provider_name}},
                component_settings={"fetch": {provider_name: {}}},
                global_middleware=[],
                middleware={},
                middleware_settings={},
                max_concurrency=2,
            ),
            discovery_source=RealDiscoverySource(),
        )
        await app.start()
        try:
            result = await app.run_pipeline_detailed(pipeline, inputs={"url": "https://example.com"})
        finally:
            await app.shutdown()
        assert result.outcome.value == "succeeded"
        return result.results["fetch_homepage"].payload.content

    httpx_content = await run_with_provider("httpx")
    playwright_content = await run_with_provider("playwright")

    assert httpx_content == b"httpx"
    assert playwright_content == b"playwright"
