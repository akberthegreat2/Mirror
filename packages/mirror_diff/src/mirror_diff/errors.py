"""Diff capability exceptions."""

from mirror_core.exceptions import MirrorError


class DiffError(MirrorError):
    """Raised when a diff operation fails."""
