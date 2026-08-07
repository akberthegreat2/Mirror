"""Mirror Dedup capability – remove deterministic duplicate documents."""

from mirror_dedup.capability import capability
from mirror_dedup.errors import DedupError
from mirror_dedup.models import (
    DedupDecision,
    DedupDocument,
    DeduplicatedDocument,
    DedupRequest,
    DedupResult,
)
from mirror_dedup.protocol import Deduplicator
from mirror_dedup.runner import dedup_step
from mirror_dedup.settings import DedupSettings

__all__ = [
    "DedupDecision",
    "DedupDocument",
    "DedupError",
    "DedupRequest",
    "DedupResult",
    "DedupSettings",
    "DeduplicatedDocument",
    "Deduplicator",
    "capability",
    "dedup_step",
]
