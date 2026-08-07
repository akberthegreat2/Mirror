"""Capability descriptor for Archive."""

from mirror_core.extensions.models import CapabilityManifest

from mirror_archive.models import ArchiveRequest, ArchiveResult
from mirror_archive.protocol import Archive
from mirror_archive.settings import ArchiveSettings

capability = CapabilityManifest(
    name="archive",
    api_version="1.0",
    protocol=Archive,
    request_model=ArchiveRequest,
    result_model=ArchiveResult,
    settings_model=ArchiveSettings,
    runner="mirror_archive.runner:archive_step",
    input_ports={},
    output_ports={"result": ArchiveResult},
    metadata={
        "description": "Persist resources durably to storage backends",
        "examples": [
            {"resource_id": "123e4567-e89b-12d3-a456-426614174000"},
        ],
    },
)
