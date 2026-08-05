"""Metadata and blob storage contracts for Mirror.

These protocols and their in-memory implementations follow the same
precedent ``docs/WORKER_CONTRACT.md`` sets for worker backends: the contract
lives in frozen core so capability packages (e.g. ``mirror_crawl``) can
depend on a stable type without depending on any particular backend, and an
in-memory implementation ships alongside it for local development and tests.

Production-lean backends (SQLite, filesystem) are a beta-stage concern and
live in ``mirror_core.beta.storage`` instead — see that module for why.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field


class MetadataRecord(BaseModel):
    """Structured metadata row used by crawlers, schedulers, and workers."""

    model_config = ConfigDict(frozen=True)

    namespace: str
    key: str
    payload: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


@runtime_checkable
class MetadataStore(Protocol):
    """Persistence contract for structured metadata."""

    def put(self, record: MetadataRecord) -> None:
        ...

    def get(self, namespace: str, key: str) -> MetadataRecord | None:
        ...

    def list(self, namespace: str | None = None) -> list[MetadataRecord]:
        ...


@runtime_checkable
class BlobStore(Protocol):
    """Persistence contract for binary payloads."""

    def put_bytes(self, key: str, payload: bytes) -> None:
        ...

    def get_bytes(self, key: str) -> bytes | None:
        ...

    def delete(self, key: str) -> None:
        ...


class InMemoryMetadataStore:
    """In-memory metadata store for development and tests."""

    def __init__(self) -> None:
        self._records: dict[tuple[str, str], MetadataRecord] = {}

    def put(self, record: MetadataRecord) -> None:
        self._records[(record.namespace, record.key)] = record

    def get(self, namespace: str, key: str) -> MetadataRecord | None:
        return self._records.get((namespace, key))

    def list(self, namespace: str | None = None) -> list[MetadataRecord]:
        records = list(self._records.values())
        if namespace is None:
            return records
        return [record for record in records if record.namespace == namespace]


class InMemoryBlobStore:
    """In-memory blob store for tests."""

    def __init__(self) -> None:
        self._blobs: dict[str, bytes] = {}

    def put_bytes(self, key: str, payload: bytes) -> None:
        self._blobs[key] = payload

    def get_bytes(self, key: str) -> bytes | None:
        return self._blobs.get(key)

    def delete(self, key: str) -> None:
        self._blobs.pop(key, None)