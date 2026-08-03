"""Settings for WARC archive provider."""

from pathlib import Path

from pydantic import BaseModel, Field


class WARCSettings(BaseModel):
    """Provider-specific settings for WARC.

    Attributes:
        output_dir: Directory to write WARC files to.
        compress: Whether to compress WARC files (gzip).
        warc_version: WARC format version.
    """

    output_dir: Path = Field(default=Path("./data/archive"))
    compress: bool = True
    warc_version: str = "1.1"
