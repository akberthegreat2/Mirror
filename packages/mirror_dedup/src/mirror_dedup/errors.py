"""Deduplication capability exceptions."""

from mirror_core.exceptions import MirrorError


class DedupError(MirrorError):
    """Raised when deduplication fails."""
