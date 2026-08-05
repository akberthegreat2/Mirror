"""Settings for the WARC archive provider."""

from pathlib import Path

from pydantic import BaseModel, Field


class WARCSettings(BaseModel):
    """Provider-specific WARC writer settings."""

    output_dir: Path = Field(default=Path("./data/archive"))
    compress: bool = True
    warc_version: str = Field(default="1.1", pattern=r"^(1\.0|1\.1)$")
    max_file_bytes: int = Field(default=512 * 1024 * 1024, ge=1)
    max_records: int = Field(default=100_000, ge=1)
