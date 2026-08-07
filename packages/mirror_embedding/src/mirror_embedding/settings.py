"""Settings for the Embedding capability."""

from pydantic import BaseModel, Field, model_validator


class EmbeddingSettings(BaseModel):
    """Runtime defaults for text embeddings."""

    dimension: int = Field(default=64, ge=8, le=4096)
    normalize: bool = True

    @model_validator(mode="after")
    def validate_dimension(self) -> "EmbeddingSettings":
        """Keep the vector space reasonably sized."""

        if self.dimension % 2:
            raise ValueError("dimension should be even for stable hashing buckets")
        return self
