"""Request and response models for the Archive capability."""

from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class ArchiveRequest(BaseModel):
    """Input for an archive operation.

    Attributes:
        resource_id: UUID of the resource to archive.
        payload: The resource payload (usually a ResourceEnvelope or FetchResult).
        metadata: Additional metadata to store with the archive.
        path: Optional storage path or identifier.
    """

    resource_id: UUID
    payload: Any  # Usually a ResourceEnvelope or FetchResult
    metadata: dict[str, Any] = Field(default_factory=dict)
    path: str | None = None


class ArchiveResult(BaseModel):
    """Output of an archive operation.

    Attributes:
        archive_id: Unique identifier for the archived entry.
        path: Storage path or identifier.
        size: Size in bytes of the archived data.
        checksum: Checksum of the archived data.
        timestamp: ISO 8601 timestamp when archive completed.
    """

    archive_id: UUID
    path: str
    size: int = Field(..., ge=0)
    checksum: str | None = None
    timestamp: str  # ISO 8601
