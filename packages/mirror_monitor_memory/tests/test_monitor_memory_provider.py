import pytest
from mirror_monitor.models import MonitorRequest, MonitorResult
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


@pytest.mark.asyncio
async def test_memory_monitor_provider_works() -> None:
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
    assert isinstance(result, MonitorResult)
    assert result.snapshot.url == "https://example.com"
