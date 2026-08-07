"""Enrichment capability exceptions."""

from mirror_core.exceptions import MirrorError


class EnrichmentError(MirrorError):
    """Raised when enrichment fails."""
