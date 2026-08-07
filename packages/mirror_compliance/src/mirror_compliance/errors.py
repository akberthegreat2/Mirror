"""Compliance capability exceptions."""

from mirror_core.exceptions import MirrorError


class ComplianceError(MirrorError):
    """Raised when compliance evaluation fails."""
