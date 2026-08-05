"""Typed request and response models for the Archive capability."""

from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class ArchivePayload(BaseModel):
    """Canonical bytes payload accepted by archive providers."""

    content: bytes
    target_uri: str = "urn:mirror:resource"
    media_type: str = "application/octet-stream"
    headers: dict[str, str] = Field(default_factory=dict)


class ArchiveRequest(BaseModel):
    """Input for an archive operation."""

    resource_id: UUID
    payload: ArchivePayload
    metadata: dict[str, Any] = Field(default_factory=dict)
    path: str | None = None


class ArchiveResult(BaseModel):
    """Output of an archive operation."""

    archive_id: UUID
    path: str
    size: int = Field(..., ge=0)
    checksum: str | None = None
    timestamp: str
