"""Diff runner – adapts a resolved provider to the capability contract."""

from __future__ import annotations

from .errors import DiffError
from .models import DiffRequest, DiffResult
from .protocol import Diff


async def diff_step(provider: Diff, request: DiffRequest) -> DiffResult:
    try:
        return await provider.diff(request)
    except DiffError:
        raise
    except Exception as exc:
        raise DiffError("Failed to compute diff", cause=exc) from exc
