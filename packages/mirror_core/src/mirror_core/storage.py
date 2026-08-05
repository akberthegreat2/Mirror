"""Metadata and blob storage contracts for Mirror beta workflows."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
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


class SQLiteMetadataStore:
    """SQLite-backed metadata store for beta development."""

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        self._conn = sqlite3.connect(self._path)
        self._conn.row_factory = sqlite3.Row
        self._ensure_schema()

    def put(self, record: MetadataRecord) -> None:
        self._conn.execute(
            """
            INSERT INTO metadata(namespace, key, payload, created_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(namespace, key)
            DO UPDATE SET payload = excluded.payload,
                          created_at = excluded.created_at
            """,
            (
                record.namespace,
                record.key,
                json.dumps(record.payload, sort_keys=True),
                record.created_at.isoformat(),
            ),
        )
        self._conn.commit()

    def get(self, namespace: str, key: str) -> MetadataRecord | None:
        row = self._conn.execute(
            "SELECT namespace, key, payload, created_at FROM metadata WHERE namespace = ? AND key = ?",
            (namespace, key),
        ).fetchone()
        if row is None:
            return None
        return MetadataRecord(
            namespace=row["namespace"],
            key=row["key"],
            payload=json.loads(row["payload"]),
            created_at=datetime.fromisoformat(row["created_at"]),
        )

    def list(self, namespace: str | None = None) -> list[MetadataRecord]:
        if namespace is None:
            rows = self._conn.execute(
                "SELECT namespace, key, payload, created_at FROM metadata ORDER BY namespace, key"
            ).fetchall()
        else:
            rows = self._conn.execute(
                """
                SELECT namespace, key, payload, created_at
                FROM metadata
                WHERE namespace = ?
                ORDER BY namespace, key
                """,
                (namespace,),
            ).fetchall()
        return [
            MetadataRecord(
                namespace=row["namespace"],
                key=row["key"],
                payload=json.loads(row["payload"]),
                created_at=datetime.fromisoformat(row["created_at"]),
            )
            for row in rows
        ]

    def close(self) -> None:
        self._conn.close()

    def _ensure_schema(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS metadata (
                namespace TEXT NOT NULL,
                key TEXT NOT NULL,
                payload TEXT NOT NULL,
                created_at TEXT NOT NULL,
                PRIMARY KEY(namespace, key)
            )
            """
        )
        self._conn.commit()


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


class FileSystemBlobStore:
    """Filesystem blob store for local beta workflows."""

    def __init__(self, base_path: str | Path) -> None:
        self._base_path = Path(base_path)
        self._base_path.mkdir(parents=True, exist_ok=True)

    def put_bytes(self, key: str, payload: bytes) -> None:
        path = self._resolve(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)

    def get_bytes(self, key: str) -> bytes | None:
        path = self._resolve(key)
        if not path.exists():
            return None
        return path.read_bytes()

    def delete(self, key: str) -> None:
        path = self._resolve(key)
        if path.exists():
            path.unlink()

    def _resolve(self, key: str) -> Path:
        parts = [part for part in Path(key).parts if part not in {"..", ".", ""}]
        if not parts:
            raise ValueError("Blob key must not be empty")
        return self._base_path.joinpath(*parts)
