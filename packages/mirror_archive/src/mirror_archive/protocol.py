"""Archive capability protocol."""

from typing import Protocol, runtime_checkable

from mirror_archive.models import ArchiveRequest, ArchiveResult


@runtime_checkable
class Archive(Protocol):
    """Protocol for archive providers.

    Implementations persist resources durably to storage backends
    (WARC, filesystem, S3, etc.).
    """

    async def archive(self, request: ArchiveRequest) -> ArchiveResult:
        """Archive a resource.

        Args:
            request: ArchiveRequest with resource and options.

        Returns:
            ArchiveResult with archive metadata.

        Raises:
            ArchiveError: If the archive operation fails.
        """
        ...
