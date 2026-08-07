"""Archive step runner – adapts pipeline inputs to provider contract."""

from __future__ import annotations

from mirror_core.executor_support import RunnerContext

from mirror_archive.exceptions import ArchiveError
from mirror_archive.models import ArchiveRequest, ArchiveResult
from mirror_archive.protocol import Archive


async def archive_step(
    provider: Archive,
    request: ArchiveRequest,
    runner_context: RunnerContext | None = None,
) -> ArchiveResult:
    """Adapt an Archive provider to the capability runner contract."""
    try:
        return await provider.archive(request)
    except ArchiveError:
        raise
    except Exception as exc:
        raise ArchiveError(
            f"Failed to archive {request.resource_id}: {exc}",
            details={"resource_id": str(request.resource_id)},
            cause=exc,
        ) from exc
