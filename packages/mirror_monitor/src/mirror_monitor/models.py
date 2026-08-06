"""Typed monitor-domain models."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from pydantic import BaseModel, Field


@dataclass(slots=True, frozen=True)
class MonitorSnapshot:
    url: str
    fetched_at: datetime
    status_code: int | None
    etag: str | None
    last_modified: str | None
    body_sha256: str
    changed: bool
    previous_sha256: str | None = None


class MonitorRequest(BaseModel):
    url: str = Field(min_length=1)
    headers: dict[str, str] = Field(default_factory=dict)


class MonitorResult(BaseModel):
    snapshot: MonitorSnapshot
