"""Diff runner – adapts a resolved provider to the capability contract."""

from __future__ import annotations

from mirror_core.executor_support import RunnerContext

from .errors import DiffError
from .models import DiffRequest, DiffResult
from .protocol import Diff


async def diff_step(
    provider: Diff, request: DiffRequest, runner_context: RunnerContext | None = None
) -> DiffResult:
    """Adapt a Diff provider to the capability runner contract."""
    try:
        return await provider.diff(request)
    except DiffError:
        raise
    except Exception as exc:
        raise DiffError("Failed to compute diff", cause=exc) from exc
