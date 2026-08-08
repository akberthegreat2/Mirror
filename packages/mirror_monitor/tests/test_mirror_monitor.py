"""Tests for the monitor capability package."""

from __future__ import annotations

import pytest
from mirror_monitor import MonitorRequest, MonitorResult, capability, monitor_step
from mirror_monitor_memory import (
    ContentMonitor,
    MemoryMonitorProvider,
    MemoryMonitorStateStore,
)


class FakeResponse:
    def __init__(
        self,
        url: str,
        body: str,
        *,
        status_code: int = 200,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.url = url
        self._body = body.encode()
        self.status_code = status_code
        self.headers = headers or {"content-type": "text/html"}

    @property
    def content(self) -> bytes:
        return self._body


class FakeClient:
    def __init__(self, pages: dict[str, FakeResponse]) -> None:
        self.pages = pages

    async def get(
        self, url: str, *, headers: dict[str, str] | None = None
    ) -> FakeResponse:
        return self.pages[url]


class FakeMonitorProvider:
    def __init__(self, monitor: ContentMonitor) -> None:
        self.monitor = monitor

    async def check(self, request: MonitorRequest) -> MonitorResult:
        snapshot = await self.monitor.check(request.url)
        return MonitorResult(snapshot=snapshot)


def test_capability_descriptor() -> None:
    assert capability.name == "monitor"
    assert capability.request_model == MonitorRequest
    assert capability.result_model == MonitorResult
    assert capability.runner == "mirror_monitor.runner:monitor_step"


@pytest.mark.asyncio
async def test_content_monitor_tracks_state() -> None:
    monitor = ContentMonitor(
        client=FakeClient(
            {
                "https://example.com": FakeResponse(
                    "https://example.com", "<html>a</html>"
                )
            }
        ),
        state_store=MemoryMonitorStateStore(),
    )
    snapshot = await monitor.check("https://example.com")
    assert snapshot.url == "https://example.com"
    assert snapshot.fetched_at.tzinfo is not None
    assert snapshot.changed is True


@pytest.mark.asyncio
async def test_monitor_step() -> None:
    monitor = ContentMonitor(
        client=FakeClient(
            {
                "https://example.com": FakeResponse(
                    "https://example.com", "<html>a</html>"
                )
            }
        ),
        state_store=MemoryMonitorStateStore(),
    )
    result = await monitor_step(
        FakeMonitorProvider(monitor), MonitorRequest(url="https://example.com")
    )
    assert result.snapshot.url == "https://example.com"


@pytest.mark.asyncio
async def test_memory_monitor_provider() -> None:
    monitor = ContentMonitor(
        client=FakeClient(
            {
                "https://example.com": FakeResponse(
                    "https://example.com", "<html>a</html>"
                )
            }
        ),
        state_store=MemoryMonitorStateStore(),
    )
    result = await MemoryMonitorProvider(monitor).check(
        MonitorRequest(url="https://example.com")
    )
    assert result.snapshot.url == "https://example.com"
