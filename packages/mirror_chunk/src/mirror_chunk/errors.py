"""Chunking capability exceptions."""

from mirror_core.exceptions import MirrorError


class ChunkError(MirrorError):
    """Raised when chunking fails."""
