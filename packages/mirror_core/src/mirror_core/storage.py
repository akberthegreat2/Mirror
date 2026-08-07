"""Blob storage contracts and durable local blob backends.

Metadata persistence now lives in :mod:`mirror_core.metadata`. This module keeps
blob storage focused and re-exports the metadata contract for compatibility.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

from mirror_core.metadata import (
    InMemoryMetadataStore,
    MetadataNamespaces,
    MetadataRecord,
    MetadataStore,
    SQLiteMetadataStore,
)


@runtime_checkable
class BlobStore(Protocol):
    """Persistence contract for binary blobs."""

    def put_bytes(self, key: str, payload: bytes) -> None: ...

    def get_bytes(self, key: str) -> bytes | None: ...

    def delete(self, key: str) -> None: ...


class InMemoryBlobStore:
    """In-memory blob store for tests and local development."""

    def __init__(self) -> None:
        self._blobs: dict[str, bytes] = {}

    def put_bytes(self, key: str, payload: bytes) -> None:
        self._blobs[_normalize_blob_key(key)] = payload

    def get_bytes(self, key: str) -> bytes | None:
        return self._blobs.get(_normalize_blob_key(key))

    def delete(self, key: str) -> None:
        self._blobs.pop(_normalize_blob_key(key), None)


class FileSystemBlobStore:
    """Filesystem blob store for durable local workflows."""

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
        return _resolve_blob_path(self._base_path, key)


def _normalize_blob_key(key: str) -> str:
    _resolve_blob_path(Path("."), key)
    return key


def _resolve_blob_path(base_path: Path, key: str) -> Path:
    candidate = Path(key)
    if (
        candidate.is_absolute()
        or any(part in {"..", "."} for part in candidate.parts)
        or not candidate.parts
    ):
        raise ValueError("Blob key must be a relative path without traversal segments")
    return base_path.joinpath(*candidate.parts)


__all__ = [
    "BlobStore",
    "FileSystemBlobStore",
    "InMemoryBlobStore",
    "InMemoryMetadataStore",
    "MetadataNamespaces",
    "MetadataRecord",
    "MetadataStore",
    "SQLiteMetadataStore",
]
