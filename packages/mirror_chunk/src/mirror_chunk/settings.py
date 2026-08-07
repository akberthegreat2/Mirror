"""Settings for the Chunking capability."""

from pydantic import BaseModel, Field, model_validator


class ChunkSettings(BaseModel):
    """Runtime defaults for text chunking."""

    chunk_size: int = Field(default=128, ge=1, le=4096)
    chunk_overlap: int = Field(default=16, ge=0, le=2048)

    @model_validator(mode="after")
    def validate_overlap(self) -> "ChunkSettings":
        """Ensure the overlap is smaller than the chunk size."""

        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size")
        return self
