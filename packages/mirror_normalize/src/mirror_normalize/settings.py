"""Settings for the Normalization capability."""

from typing import Literal

from pydantic import BaseModel


class NormalizationSettings(BaseModel):
    """Runtime defaults for text normalization."""

    lowercase: bool = True
    collapse_whitespace: bool = True
    strip_edges: bool = True
    unicode_form: Literal["NFC", "NFKC", "NFD", "NFKD"] = "NFKC"
