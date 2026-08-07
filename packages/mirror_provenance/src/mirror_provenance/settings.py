"""Settings for the Provenance capability."""

from pydantic import BaseModel, Field


class ProvenanceSettings(BaseModel):
    """Runtime defaults for provenance envelope creation."""

    default_schema_version: str = Field(default="1.0", min_length=1)
