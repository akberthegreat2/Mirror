"""Memory-backed monitor provider."""

from __future__ import annotations

from mirror_core.registry import ProviderConfig
from mirror_monitor.models import MonitorRequest, MonitorResult
from mirror_monitor.protocol import Monitor

from .monitor import ContentMonitor


class MemoryMonitorProvider(Monitor):
    def __init__(self, monitor: ContentMonitor | None = None) -> None:
        self._monitor = monitor or ContentMonitor()

    async def check(self, request: MonitorRequest) -> MonitorResult:
        snapshot = await self._monitor.check(request.url)
        return MonitorResult(snapshot=snapshot)


provider = ProviderConfig(
    name="memory",
    capability="monitor",
    capability_api="~=1.0",
    factory="mirror_monitor_memory.provider:MemoryMonitorProvider",
    metadata={"description": "Memory-backed monitor provider."},
)
