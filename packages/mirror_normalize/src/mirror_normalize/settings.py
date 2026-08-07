"""Settings for the Normalization capability."""

from pydantic import BaseModel, Field


class NormalizationSettings(BaseModel):
    """Runtime defaults for text normalization."""

    lowercase: bool = True
    collapse_whitespace: bool = True
    strip_edges: bool = True
    unicode_form: str = Field(default="NFKC", pattern=r"^(NFC|NFKC|NFD|NFKD)$")
