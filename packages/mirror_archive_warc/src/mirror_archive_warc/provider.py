"""WARC archive provider implementation."""

from __future__ import annotations

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
    """Archive provider using WARC format.

    Implements both AsyncLifecycle and the Archive protocol.
    Writes resources to WARC files using warcio.
    """

    def __init__(self, settings: WARCSettings | None = None) -> None:
        self._settings = settings or WARCSettings()
        self._output_dir = self._settings.output_dir
        self._writer: Any = None
        self._current_file: Path | None = None
        self._file: BufferedWriter | None = None

    @staticmethod
    def _require_warcio() -> tuple[Any, Any]:
        try:
            from warcio.statusandheaders import StatusAndHeaders
            from warcio.warcwriter import WARCWriter
        except ImportError as exc:  # pragma: no cover - exercised in package tests
            raise ArchiveError(
                "WARC provider requires the optional 'warcio' dependency"
            ) from exc
        return StatusAndHeaders, WARCWriter

    async def setup(self) -> None:
        """Initialize the WARC writer."""
        self._output_dir.mkdir(parents=True, exist_ok=True)
        StatusAndHeaders, WARCWriter = self._require_warcio()

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        filename = (
            f"mirror-{timestamp}.warc.gz" if self._settings.compress else f"mirror-{timestamp}.warc"
        )
        self._current_file = self._output_dir / filename
        self._file = open(self._current_file, "wb")  # noqa: SIM115
        self._writer = WARCWriter(self._file, gzip=self._settings.compress)
        self._status_headers_cls = StatusAndHeaders

    async def teardown(self) -> None:
        """Close the WARC writer and file."""
        if self._writer is not None:
            if self._file is not None:
                self._file.close()
            self._writer = None
            self._file = None
            self._current_file = None

    async def archive(self, request: ArchiveRequest) -> ArchiveResult:
        """Archive a resource to the WARC file.

        Args:
            request: ArchiveRequest with resource payload and metadata.

        Returns:
            ArchiveResult with archive metadata.

        Raises:
            ArchiveError: If the archive operation fails.
        """
        if self._writer is None:
            await self.setup()
        assert self._writer is not None
        status_headers_cls = getattr(self, "_status_headers_cls", None)
        if status_headers_cls is None:
            raise ArchiveError("WARC provider is not initialized correctly")

        try:
            payload = request.payload
            if payload is None:
                raise ArchiveError("Invalid payload: None is not archivable")

            content = b""
            url = ""
            if hasattr(payload, "content"):
                content = payload.content
                url = getattr(payload, "url", "unknown")
            elif hasattr(payload, "payload"):
                inner = payload.payload
                if hasattr(inner, "content"):
                    content = inner.content
                    url = getattr(inner, "url", "unknown")
            else:
                content = payload if isinstance(payload, bytes) else str(payload).encode()

            headers_list = [
                (b"Content-Type", b"application/octet-stream"),
                (b"WARC-Record-ID", f"<urn:uuid:{uuid4()}>".encode()),
                (b"WARC-Date", datetime.now(timezone.utc).isoformat().encode()),
                (b"WARC-Payload-Digest", f"sha256:{hashlib.sha256(content).hexdigest()}".encode()),
                (b"WARC-Type", b"resource"),
                (b"WARC-Target-URI", url.encode()),
            ]

            if request.metadata:
                for key, value in request.metadata.items():
                    headers_list.append((f"Mirror-Metadata-{key}".encode(), str(value).encode()))

            status_headers = status_headers_cls("200 OK", headers_list)
            payload_stream = io.BytesIO(content)
            record = self._writer.create_warc_record(
                uri=url,
                record_type="resource",
                payload=payload_stream,
                http_headers=status_headers,
            )
            self._writer.write_record(record)

            return ArchiveResult(
                archive_id=uuid4(),
                path=str(self._current_file),
                size=len(content),
                checksum=f"sha256:{hashlib.sha256(content).hexdigest()}",
                timestamp=datetime.now(timezone.utc).isoformat(timespec="seconds"),
            )
        except Exception as exc:
            if isinstance(exc, ArchiveError):
                raise
            raise ArchiveError(f"Failed to archive {request.resource_id}: {exc}", cause=exc) from exc
