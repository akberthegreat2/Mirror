"""Monitor capability protocol."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from .models import MonitorRequest, MonitorResult


@runtime_checkable
class Monitor(Protocol):
    async def check(self, request: MonitorRequest) -> MonitorResult: ...
