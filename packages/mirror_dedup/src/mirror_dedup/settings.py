"""Settings for the Deduplication capability."""

from typing import Literal

from pydantic import BaseModel, Field


class DedupSettings(BaseModel):
    """Runtime defaults for deterministic document deduplication."""

    unicode_form: Literal["NFC", "NFKC", "NFD", "NFKD"] = "NFKC"
    collapse_whitespace: bool = Field(default=True)
    casefold: bool = Field(default=True)
    fingerprint_metadata_keys: tuple[str, ...] = Field(default_factory=tuple)
