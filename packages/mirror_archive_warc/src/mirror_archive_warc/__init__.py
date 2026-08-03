"""WARC provider for Mirror Archive capability."""

from mirror_core.registry import ProviderConfig

from mirror_archive_warc.provider import WARCProvider
from mirror_archive_warc.settings import WARCSettings

provider = ProviderConfig(
    name="warc",
    capability="archive",
    capability_api="~=1.0",
    factory="mirror_archive_warc.provider:WARCProvider",
    settings_model="mirror_archive_warc.settings:WARCSettings",
    features=["warc", "compression", "checksum"],
    priority=100,
    metadata={
        "description": "WARC file writer",
        "requires_filesystem": True,
    },
)

__all__ = ["WARCProvider", "WARCSettings", "provider"]
