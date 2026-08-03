"""Mirror core exception hierarchy.

Core defines only generic exceptions. Capability-specific errors
(FetchError, ArchiveError, etc.) are defined in their respective
packages and inherit from MirrorError.
"""

from typing import Any, Optional


class MirrorError(Exception):
    """Base exception for all Mirror errors."""

    def __init__(
        self,
        message: str,
        details: Optional[dict[str, Any]] = None,
        cause: Optional[Exception] = None,
    ) -> None:
        self.message = message
        self.details = details or {}
        self.cause = cause
        if cause:
            self.__cause__ = cause
        super().__init__(message)


class ConfigurationError(MirrorError):
    """Raised when configuration is invalid or cannot be resolved."""


class LifecycleError(MirrorError):
    """Raised when component setup or teardown fails."""


class DiscoveryError(MirrorError):
    """Raised when extension discovery fails (entry points, descriptors)."""


class RegistryError(MirrorError):
    """Raised when descriptor registration or lookup fails."""


class ValidationError(MirrorError):
    """Raised when data validation fails (type mismatches, missing fields)."""


class PlannerError(MirrorError):
    """Raised when pipeline compilation fails (cycle, invalid binding)."""


class ExecutionError(MirrorError):
    """Raised when pipeline execution fails."""