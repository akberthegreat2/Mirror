"""Provenance capability exceptions."""

from mirror_core.exceptions import MirrorError


class ProvenanceError(MirrorError):
    """Raised when provenance envelope creation fails."""
