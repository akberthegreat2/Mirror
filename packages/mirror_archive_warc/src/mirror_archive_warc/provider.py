"""Concurrent-safe WARC archive provider implementation."""

from __future__ import annotations

import asyncio
import hashlib
import io
from datetime import datetime, timezone
from io import BufferedWriter
from pathlib import Path
from typing import Any
from uuid import uuid4

from mirror_archive.exceptions import ArchiveError
from mirror_archive.models import ArchiveRequest, ArchiveResult
from mirror_archive.protocol import Archive
from mirror_core.lifecycle import AsyncLifecycle

from mirror_archive_warc.settings import WARCSettings


class WARCProvider(AsyncLifecycle, Archive):
    """Write typed archive payloads to rotating WARC files."""

    def __init__(self, settings: WARCSettings | None = None) -> None:
        self._settings = settings or WARCSettings()
        self._output_dir = self._settings.output_dir
        self._writer: Any = None
        self._current_file: Path | None = None
        self._file: BufferedWriter | None = None
        self._status_headers_cls: Any = None
        self._lock = asyncio.Lock()
        self._records = 0
        self._bytes = 0

    @staticmethod
    def _require_warcio() -> tuple[Any, Any]:
        try:
            from warcio.statusandheaders import StatusAndHeaders
            from warcio.warcwriter import WARCWriter
        except ImportError as exc:
            raise ArchiveError("WARC provider requires the 'warcio' dependency") from exc
        return StatusAndHeaders, WARCWriter

    async def setup(self) -> None:
        """Initialize one writer; repeated setup calls are no-ops."""
        async with self._lock:
            if self._writer is not None:
                return
            await asyncio.to_thread(self._open_segment)

    def _open_segment(self) -> None:
        self._output_dir.mkdir(parents=True, exist_ok=True)
        status_headers, writer_cls = self._require_warcio()
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f")
        suffix = ".warc.gz" if self._settings.compress else ".warc"
        self._current_file = self._output_dir / f"mirror-{timestamp}-{uuid4().hex[:8]}{suffix}"
        self._file = self._current_file.open("wb")
        self._writer = writer_cls(self._file, gzip=self._settings.compress)
        self._status_headers_cls = status_headers
        self._records = 0
        self._bytes = 0

    async def teardown(self) -> None:
        """Close the active segment idempotently."""
        async with self._lock:
            await asyncio.to_thread(self._close_segment)

    def _close_segment(self) -> None:
        if self._file is not None:
            self._file.close()
        self._writer = None
        self._file = None
        self._current_file = None
        self._status_headers_cls = None
        self._records = 0
        self._bytes = 0

    async def archive(self, request: ArchiveRequest) -> ArchiveResult:
        """Write one typed payload without implicitly starting the provider."""
        async with self._lock:
            if self._writer is None or self._status_headers_cls is None:
                raise ArchiveError("WARC provider is not initialized; call setup() first")
            if self._should_rotate(len(request.payload.content)):
                await asyncio.to_thread(self._close_segment)
                await asyncio.to_thread(self._open_segment)
            return await asyncio.to_thread(self._write_request, request)

    def _should_rotate(self, incoming_bytes: int) -> bool:
        return self._records >= self._settings.max_records or self._bytes + incoming_bytes > self._settings.max_file_bytes

    def _write_request(self, request: ArchiveRequest) -> ArchiveResult:
        assert self._writer is not None and self._status_headers_cls is not None and self._current_file is not None
        try:
            content = request.payload.content
            digest = hashlib.sha256(content).hexdigest()
            headers = [
                (b"Content-Type", request.payload.media_type.encode("ascii", "strict")),
                (b"WARC-Record-ID", f"<urn:uuid:{uuid4()}>".encode()),
                (b"WARC-Date", datetime.now(timezone.utc).isoformat().encode()),
                (b"WARC-Payload-Digest", f"sha256:{digest}".encode()),
                (b"WARC-Type", b"resource"),
                (b"WARC-Target-URI", request.payload.target_uri.encode("utf-8")),
            ]
            for key, value in request.metadata.items():
                safe_key = "".join(ch for ch in str(key) if ch.isalnum() or ch in "-_")[:64]
                if safe_key:
                    headers.append((f"Mirror-Metadata-{safe_key}".encode(), str(value).replace("\r", " ").replace("\n", " ").encode("utf-8")))
            status_headers = self._status_headers_cls("200 OK", headers)
            record = self._writer.create_warc_record(uri=request.payload.target_uri, record_type="resource",
                payload=io.BytesIO(content), http_headers=status_headers)
            self._writer.write_record(record)
            self._records += 1
            self._bytes += len(content)
            return ArchiveResult(archive_id=uuid4(), path=str(self._current_file), size=len(content),
                checksum=f"sha256:{digest}", timestamp=datetime.now(timezone.utc).isoformat(timespec="seconds"))
        except ArchiveError:
            raise
        except Exception as exc:
            raise ArchiveError(f"Failed to archive {request.resource_id}: {exc}", cause=exc) from exc
