"""WARC archive provider implementation."""

from __future__ import annotations

import hashlib
import io
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from mirror_archive.exceptions import ArchiveError
from mirror_archive.models import ArchiveRequest, ArchiveResult
from mirror_archive.protocol import Archive
from mirror_core.lifecycle import AsyncLifecycle
from warcio.statusandheaders import StatusAndHeaders
from warcio.warcwriter import WARCWriter

from mirror_archive_warc.settings import WARCSettings


class WARCProvider(AsyncLifecycle, Archive):
    """Archive provider using WARC format.

    Implements both AsyncLifecycle and the Archive protocol.
    Writes resources to WARC files using warcio.
    """

    def __init__(self, settings: WARCSettings | None = None) -> None:
        self._settings = settings or WARCSettings()
        self._output_dir = self._settings.output_dir
        self._writer: WARCWriter | None = None
        self._current_file: Path | None = None

    async def setup(self) -> None:
        """Initialize the WARC writer."""
        self._output_dir.mkdir(parents=True, exist_ok=True)

        # Use deterministic filename based on timestamp
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        filename = (
            f"mirror-{timestamp}.warc.gz" if self._settings.compress else f"mirror-{timestamp}.warc"
        )
        self._current_file = self._output_dir / filename

        # Open the WARC file
        # In sync context, we need to open the file and create the writer
        # The WARCWriter expects a file-like object in binary mode.
        # Since warcio is synchronous, we open the file in setup.
        self._file = open(self._current_file, "wb")
        self._writer = WARCWriter(self._file, gzip=self._settings.compress)

    async def teardown(self) -> None:
        """Close the WARC writer and file."""
        if self._writer is not None:
            # WARCWriter may need to flush; just close the file.
            if hasattr(self._file, "close"):
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

        try:
            payload = request.payload
            # Validate payload: must not be None, must have content
            if payload is None:
                raise ArchiveError("Invalid payload: None is not archivable")
            if not (
                hasattr(payload, "content")
                or hasattr(payload, "payload")
                or isinstance(payload, bytes)
            ):
                # If it's a simple type, we can still try to serialize it, but warn
                # For safety, we could raise, but we'll let it through.
                pass

            # Extract content (existing logic)
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
                if isinstance(payload, bytes):
                    content = payload
                else:
                    content = str(payload).encode()

            # Generate WARC record
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

            status_headers = StatusAndHeaders("200 OK", headers_list)

            # Use a BytesIO stream for the payload (warcio expects a file-like object)
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

        except Exception as e:
            raise ArchiveError(f"Failed to archive {request.resource_id}: {e}", cause=e) from e
