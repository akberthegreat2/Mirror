"""Monitor capability exceptions."""

from mirror_core.exceptions import MirrorError


class MonitorError(MirrorError):
    """Raised when a monitoring operation fails."""
