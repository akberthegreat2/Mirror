"""Archive step runner – adapts pipeline inputs to provider contract."""

from __future__ import annotations

from typing import Any

from mirror_archive.exceptions import ArchiveError
from mirror_archive.models import ArchiveRequest, ArchiveResult
from mirror_archive.protocol import Archive


async def archive_step(
    provider: Archive,
    request: ArchiveRequest,
    settings: Any | None = None,
    signal_bus: Any | None = None,
    step_id: str | None = None,
) -> ArchiveResult:
    del settings, signal_bus, step_id
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
