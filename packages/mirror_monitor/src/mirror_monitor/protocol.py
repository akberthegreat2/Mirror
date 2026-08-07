"""Monitor capability protocol."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from .models import MonitorRequest, MonitorResult


@runtime_checkable
class Monitor(Protocol):
    """Protocol for monitor providers."""

    async def check(self, request: MonitorRequest) -> MonitorResult: ...
