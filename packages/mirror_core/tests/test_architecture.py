"""Architecture-level regression tests."""

from __future__ import annotations

import inspect
from pathlib import Path

import mirror_cli.main as cli_main
import mirror_core.toml as core_toml
from mirror_analyze import capability as analyze_capability
from mirror_crawl_local.provider import LocalCrawlProvider
from mirror_diff import capability as diff_capability
from mirror_monitor import capability as monitor_capability
from mirror_scrape import capability as scrape_capability
from mirror_search import capability as search_capability

ROOT = Path(__file__).resolve().parents[3]
CAPABILITY_PACKAGES = (
    "mirror_archive",
    "mirror_crawl",
    "mirror_fetch",
    "mirror_search",
    "mirror_analyze",
    "mirror_scrape",
    "mirror_diff",
    "mirror_monitor",
)
FORBIDDEN_FRAMEWORK_FILES = {
    "runtime.py",
    "middleware.py",
    "pipeline.py",
    "executor.py",
    "planner.py",
    "signals.py",
    "registry.py",
    "lifecycle.py",
}

FORBIDDEN_CAPABILITY_HELPERS = {
    "search.py",
    "analyze.py",
    "scrape.py",
    "diff.py",
    "monitor.py",
    "services.py",
}


def test_core_owns_middleware_contract_and_builtins() -> None:
    from mirror_core.middleware import (
        MiddlewareChain,
        MiddlewareContext,
        MiddlewareInvocation,
    )
    from mirror_core.middleware.builtin import (
        LoggingMiddleware,
        RateLimitMiddleware,
        RetryMiddleware,
        TimeoutMiddleware,
        TracingMiddleware,
    )
    from mirror_core.middleware.builtin.retry import middleware as retry_middleware

    assert MiddlewareChain.__name__ == "MiddlewareChain"
    assert MiddlewareContext.__name__ == "MiddlewareContext"
    assert MiddlewareInvocation.__name__ == "MiddlewareInvocation"
    assert RetryMiddleware.__name__ == "RetryMiddleware"
    assert TimeoutMiddleware.__name__ == "TimeoutMiddleware"
    assert RateLimitMiddleware.__name__ == "RateLimitMiddleware"
    assert LoggingMiddleware.__name__ == "LoggingMiddleware"
    assert TracingMiddleware.__name__ == "TracingMiddleware"
    assert retry_middleware.factory.startswith("mirror_core.middleware.builtin")


def test_public_toml_helper_is_used() -> None:
    source = inspect.getsource(cli_main._load_mapping)
    assert "mirror_core.toml" in source
    assert "mirror_core._toml" not in source
    assert hasattr(core_toml, "load") and hasattr(core_toml, "loads")


def test_settings_modules_exist_for_phase_two_capabilities() -> None:
    from mirror_analyze.settings import AnalyzeSettings
    from mirror_diff.settings import DiffSettings
    from mirror_monitor.settings import MonitorSettings
    from mirror_scrape.settings import ScrapeSettings
    from mirror_search.settings import SearchSettings

    assert AnalyzeSettings.__name__ == "AnalyzeSettings"
    assert DiffSettings.__name__ == "DiffSettings"
    assert MonitorSettings.__name__ == "MonitorSettings"
    assert ScrapeSettings.__name__ == "ScrapeSettings"
    assert SearchSettings.__name__ == "SearchSettings"


def test_first_party_providers_conform_to_protocols() -> None:
    from mirror_analyze.protocol import Analyze
    from mirror_analyze_basic.provider import BasicAnalyzeProvider
    from mirror_archive.protocol import Archive
    from mirror_archive_warc.provider import WARCProvider
    from mirror_crawl.protocol import Crawl
    from mirror_crawl_local.provider import LocalCrawlProvider
    from mirror_diff.protocol import Diff
    from mirror_diff_text.provider import TextDiffProvider
    from mirror_fetch.protocol import Fetch
    from mirror_fetch_httpx.provider import HTTPXProvider
    from mirror_fetch_playwright.provider import PlaywrightProvider
    from mirror_monitor.protocol import Monitor
    from mirror_monitor_memory.provider import MemoryMonitorProvider
    from mirror_scrape.protocol import Scrape
    from mirror_scrape_basic.provider import BasicScrapeProvider
    from mirror_search.protocol import Search
    from mirror_search_memory.provider import SearchMemoryProvider

    class _DummyFetch(Fetch):
        async def fetch(self, request):
            raise AssertionError("unused")

    assert isinstance(HTTPXProvider(), Fetch)
    assert isinstance(PlaywrightProvider(), Fetch)
    assert isinstance(WARCProvider(), Archive)
    assert isinstance(SearchMemoryProvider(), Search)
    assert isinstance(BasicAnalyzeProvider(), Analyze)
    assert isinstance(BasicScrapeProvider(), Scrape)
    assert isinstance(TextDiffProvider(), Diff)
    assert isinstance(MemoryMonitorProvider(), Monitor)
    assert isinstance(LocalCrawlProvider(fetch=_DummyFetch()), Crawl)


def test_phase_two_descriptors_use_settings_models() -> None:
    assert search_capability.settings_model.__name__ == "SearchSettings"
    assert analyze_capability.settings_model.__name__ == "AnalyzeSettings"
    assert scrape_capability.settings_model.__name__ == "ScrapeSettings"
    assert diff_capability.settings_model.__name__ == "DiffSettings"
    assert monitor_capability.settings_model.__name__ == "MonitorSettings"


def test_crawl_provider_is_not_owner_of_dependency_lifecycle() -> None:
    assert "setup" not in LocalCrawlProvider.__dict__
    assert "teardown" not in LocalCrawlProvider.__dict__


def test_run_outcome_alias_and_contract_name_align() -> None:
    from mirror_core.executor import RunOutcome

    assert RunOutcome.PARTIALLY_SUCCEEDED.value == "partially_succeeded"
    assert RunOutcome.PARTIAL is RunOutcome.PARTIALLY_SUCCEEDED


def test_resource_envelope_is_immutable() -> None:
    from uuid import uuid4

    from mirror_core.resource import ProducerRef, ResourceEnvelope
    from pydantic import BaseModel

    class Payload(BaseModel):
        value: int

    envelope = ResourceEnvelope.create(
        resource_type="Payload",
        schema_version="1.0",
        payload=Payload(value=1),
        producer=ProducerRef(
            capability="demo",
            capability_version="1.0",
            provider="demo-provider",
        ),
        parents=[uuid4()],
        metadata={"source": "test"},
    )

    assert isinstance(envelope.parents, tuple)
    assert envelope.parents
    assert envelope.metadata["source"] == "test"

    try:
        envelope.parents += (uuid4(),)
    except Exception:
        pass
    else:
        raise AssertionError("parents should be immutable")

    try:
        envelope.metadata["source"] = "changed"  # type: ignore[index]
    except Exception:
        pass
    else:
        raise AssertionError("metadata should be immutable")

    dumped = envelope.model_dump()
    assert isinstance(dumped["parents"], list)
    assert dumped["metadata"] == {"source": "test"}


def test_no_packaging_artifacts_are_checked_in() -> None:
    bad_paths: list[str] = []
    for path in ROOT.rglob("*"):
        parts = set(path.parts)
        if (
            path.suffix == ".egg-info"
            or path.name.endswith(".egg-info")
            or "build" in parts
            or "dist" in parts
        ):
            bad_paths.append(str(path.relative_to(ROOT)))
    assert not bad_paths, f"Checked-in packaging artifacts found: {bad_paths}"


def test_capability_packages_do_not_define_framework_files() -> None:
    violations: list[str] = []
    for package in CAPABILITY_PACKAGES:
        source_root = ROOT / "packages" / package / "src" / package
        if not source_root.exists():
            continue
        for file_path in source_root.rglob("*.py"):
            if (
                file_path.name in FORBIDDEN_FRAMEWORK_FILES
                or file_path.name in FORBIDDEN_CAPABILITY_HELPERS
            ):
                violations.append(str(file_path.relative_to(ROOT)))
    assert not violations, f"Capability packages define framework files: {violations}"
