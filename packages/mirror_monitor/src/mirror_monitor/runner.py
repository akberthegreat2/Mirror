"""Monitor runner – adapts a resolved provider to the capability contract."""

from __future__ import annotations

from .errors import MonitorError
from .models import MonitorRequest, MonitorResult
from .protocol import Monitor


async def monitor_step(provider: Monitor, request: MonitorRequest) -> MonitorResult:
    try:
        return await provider.check(request)
    except MonitorError:
        raise
    except Exception as exc:
        raise MonitorError("Failed to monitor url", cause=exc) from exc
