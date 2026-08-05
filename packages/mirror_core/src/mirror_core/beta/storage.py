"""Production-lean storage backends previewed ahead of the beta release.

The contract these implement (``MetadataStore``, ``BlobStore``,
``MetadataRecord``) lives in ``mirror_core.storage`` and is stable, frozen
core surface. These SQLite- and filesystem-backed implementations are not:
see ``mirror_core.beta`` for what that means. Nothing in Mirror imports this
module unconditionally; a project that wants durable local persistence ahead
of beta opts in explicitly.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from mirror_core.storage import MetadataRecord


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
            created_at=row["created_at"],
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
                created_at=row["created_at"],
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
