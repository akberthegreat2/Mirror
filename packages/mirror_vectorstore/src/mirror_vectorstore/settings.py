"""Settings for the Vector store capability."""

from pydantic import BaseModel, Field


class VectorStoreSettings(BaseModel):
    """Runtime defaults for the vector store."""

    default_namespace: str = Field(default="default", min_length=1)
