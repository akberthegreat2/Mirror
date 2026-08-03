"""Archive capability exceptions."""

from typing import Any

from mirror_core.exceptions import MirrorError


class ArchiveError(MirrorError):
    """Raised when an archive operation fails."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
        cause: Exception | None = None,
    ) -> None:
        super().__init__(message, details=details, cause=cause)
