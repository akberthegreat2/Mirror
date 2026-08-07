"""Settings for the Compliance capability."""

from pydantic import BaseModel, Field


class ComplianceSettings(BaseModel):
    """Runtime defaults for deterministic compliance checks."""

    forbidden_terms: tuple[str, ...] = Field(default_factory=tuple)
    required_metadata_keys: tuple[str, ...] = Field(default_factory=tuple)
    max_characters: int | None = Field(default=None, ge=1)
    min_unique_words: int | None = Field(default=None, ge=1)
    case_sensitive: bool = False
