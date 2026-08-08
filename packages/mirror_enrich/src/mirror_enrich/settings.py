"""Settings for the Enrichment capability."""

from typing import Literal

from pydantic import BaseModel, Field


class EnrichmentSettings(BaseModel):
    """Runtime defaults for deterministic text enrichment."""

    unicode_form: Literal["NFC", "NFKC", "NFD", "NFKD"] = "NFKC"
    collapse_whitespace: bool = Field(default=True)
    strip_edges: bool = Field(default=True)
    summary_word_limit: int = Field(default=24, ge=1, le=128)
    max_keywords: int = Field(default=8, ge=1, le=64)
    min_keyword_length: int = Field(default=3, ge=1, le=32)
    stopwords: tuple[str, ...] = Field(
        default=(
            "a",
            "an",
            "and",
            "are",
            "as",
            "at",
            "be",
            "but",
            "by",
            "for",
            "from",
            "has",
            "have",
            "if",
            "in",
            "is",
            "it",
            "of",
            "on",
            "or",
            "that",
            "the",
            "this",
            "to",
            "was",
            "were",
            "will",
            "with",
        )
    )
