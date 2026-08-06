"""Settings for the Search capability."""

from pydantic import BaseModel, Field


class SearchSettings(BaseModel):
    """Runtime settings for search providers and indexes."""

    default_limit: int = Field(default=10, ge=1, le=100)
    index_name: str = "mirror-documents"
    result_snippet_width: int = Field(default=120, ge=20, le=500)
