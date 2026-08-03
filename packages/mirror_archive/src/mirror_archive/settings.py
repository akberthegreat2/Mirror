"""Settings for the Archive capability."""

from pydantic import BaseModel


class ArchiveSettings(BaseModel):
    """Settings for the Archive capability.

    Attributes:
        default_path: Default storage path or prefix.
        compress: Whether to compress archived data.
        checksum_algorithm: Algorithm for generating checksums.
    """

    default_path: str = "./data/archive"
    compress: bool = True
    checksum_algorithm: str = "sha256"
