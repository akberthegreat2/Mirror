"""Diff capability protocol."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from .models import DiffRequest, DiffResult


@runtime_checkable
class Diff(Protocol):
    async def diff(self, request: DiffRequest) -> DiffResult: ...
