"""Fetch capability exceptions."""

from typing import Any

from mirror_core.exceptions import MirrorError


class FetchError(MirrorError):
    """Raised when a fetch operation fails."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
        cause: Exception | None = None,
    ) -> None:
        super().__init__(message, details=details, cause=cause)
