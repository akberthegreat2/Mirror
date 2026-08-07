"""Monitor runner – adapts a resolved provider to the capability contract."""

from __future__ import annotations

from mirror_core.executor_support import RunnerContext

from .errors import MonitorError
from .models import MonitorRequest, MonitorResult
from .protocol import Monitor


async def monitor_step(
    provider: Monitor,
    request: MonitorRequest,
    runner_context: RunnerContext | None = None,
) -> MonitorResult:
    """Adapt a Monitor provider to the capability runner contract."""
    try:
        return await provider.check(request)
    except MonitorError:
        raise
    except Exception as exc:
        raise MonitorError("Failed to monitor url", cause=exc) from exc
