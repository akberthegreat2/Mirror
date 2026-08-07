"""Mirror Normalization capability – canonicalize text inputs."""

from mirror_normalize.capability import capability
from mirror_normalize.errors import NormalizationError
from mirror_normalize.models import (
    NormalizationDocument,
    NormalizationRequest,
    NormalizationResult,
    NormalizedDocument,
)
from mirror_normalize.protocol import Normalizer
from mirror_normalize.runner import normalize_step
from mirror_normalize.settings import NormalizationSettings

__all__ = [
    "NormalizationDocument",
    "NormalizationError",
    "NormalizationRequest",
    "NormalizationResult",
    "NormalizationSettings",
    "NormalizedDocument",
    "Normalizer",
    "capability",
    "normalize_step",
]
