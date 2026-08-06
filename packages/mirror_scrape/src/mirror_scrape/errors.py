"""Scrape capability exceptions."""

from mirror_core.exceptions import MirrorError


class ScrapeError(MirrorError):
    """Raised when a scrape operation fails."""
