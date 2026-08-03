"""Archive step runner – adapts pipeline inputs to provider contract."""

from __future__ import annotations

import logging
from typing import Any

from mirror_archive.exceptions import ArchiveError
from mirror_archive.models import ArchiveRequest, ArchiveResult
from mirror_archive.protocol import Archive
from mirror_archive.signals import (
    SIGNAL_ARCHIVE_FAILED,
    SIGNAL_ARCHIVE_STARTED,
    SIGNAL_ARCHIVE_SUCCEEDED,
)

logger = logging.getLogger(__name__)


async def archive_step(
    provider: Archive,
    request: ArchiveRequest,
    settings: Any | None = None,
    signal_bus: Any | None = None,
    step_id: str | None = None,
) -> ArchiveResult:
    """Run an archive step.

    Args:
        provider: Archive provider instance.
        request: ArchiveRequest with resource and options.
        settings: Optional runtime settings overrides.
        signal_bus: Optional SignalBus for emitting signals.
        step_id: Optional step identifier for signal context.

    Returns:
        ArchiveResult: The archive metadata.

    Raises:
        ArchiveError: If the archive operation fails.
    """
    resource_id = request.resource_id
    logger.debug(f"Archiving: {resource_id}")

    if signal_bus:
        await signal_bus.emit(
            SIGNAL_ARCHIVE_STARTED,
            step_id=step_id,
            resource_id=resource_id,
            request=request,
        )

    try:
        result = await provider.archive(request)

        if signal_bus:
            await signal_bus.emit(
                SIGNAL_ARCHIVE_SUCCEEDED,
                step_id=step_id,
                resource_id=resource_id,
                result=result,
            )

        return result

    except Exception as e:
        if signal_bus:
            await signal_bus.emit(
                SIGNAL_ARCHIVE_FAILED,
                step_id=step_id,
                resource_id=resource_id,
                error=str(e),
            )

        raise ArchiveError(
            f"Failed to archive {resource_id}: {e}",
            details={"resource_id": str(resource_id)},
            cause=e,
        ) from e
