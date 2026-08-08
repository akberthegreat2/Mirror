"""Install and import smoke tests for real-world package usage."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PACKAGE_PATHS = [
    ROOT / "packages" / "mirror_core",
    ROOT / "packages" / "mirror_fetch",
    ROOT / "packages" / "mirror_fetch_httpx",
    ROOT / "packages" / "mirror_fetch_playwright",
    ROOT / "packages" / "mirror_crawl",
    ROOT / "packages" / "mirror_crawl_local",
    ROOT / "packages" / "mirror_testing",
]


def _copy_package_tree(source: Path, destination: Path) -> Path:
    """Copy a package tree into a temp directory without polluting the checkout."""

    ignore = shutil.ignore_patterns("build", "dist", "*.egg-info", "__pycache__")
    shutil.copytree(source, destination, ignore=ignore)
    return destination


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

    copied_paths = [
        _copy_package_tree(path, tmp_path / path.name) for path in PACKAGE_PATHS
    ]

    install = [
        sys.executable,
        "-m",
        "pip",
        "install",
        "--no-deps",
        "--no-build-isolation",
        "--target",
        str(target),
        *(str(path) for path in copied_paths),
    ]
    subprocess.run(install, check=True, capture_output=True, text=True)

    probe = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import mirror_core, mirror_fetch, mirror_fetch_httpx, mirror_fetch_playwright, mirror_crawl, mirror_crawl_local, mirror_testing; "
                "import mirror_core.middleware; "
                "from mirror_fetch import capability; "
                "from mirror_fetch_httpx import provider as httpx_provider; "
                "from mirror_fetch_playwright import provider as playwright_provider; "
                "from mirror_crawl_local import provider as crawl_provider; "
                "print(capability.name, httpx_provider.name, playwright_provider.name, crawl_provider.name)"
            ),
        ],
        check=True,
        capture_output=True,
        text=True,
        env={
            **os.environ,
            "PYTHONPATH": os.pathsep.join(
                [str(target), "/opt/pyvenv/lib/python3.13/site-packages"]
            ),
        },
    )

    assert probe.stdout.strip() == "fetch httpx playwright local"


@pytest.mark.asyncio
async def test_real_world_fetch_pipeline_uses_actual_packages(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Run a representative Fetch pipeline using the real core and provider packages."""

    _bootstrap_source_paths()

    from mirror_core.application import Application
    from mirror_core.extensions.models import ProviderManifest
    from mirror_core.pipeline import Pipeline, Step
    from mirror_core.settings import MirrorSettings
    from mirror_fetch.capability import capability as fetch_capability
    from mirror_fetch.models import FetchRequest, FetchResult
    from mirror_fetch_httpx.provider import HTTPXProvider
    from mirror_fetch_playwright.provider import PlaywrightProvider

    class RealDiscoverySource:
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
            ], []

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
            result = await app.run_pipeline_detailed(
                pipeline, inputs={"url": "https://example.com"}
            )
        finally:
            await app.shutdown()
        assert result.outcome.value == "succeeded"
        return result.results["fetch_homepage"].payload.content

    httpx_content = await run_with_provider("httpx")
    playwright_content = await run_with_provider("playwright")

    assert httpx_content == b"httpx"
    assert playwright_content == b"playwright"
