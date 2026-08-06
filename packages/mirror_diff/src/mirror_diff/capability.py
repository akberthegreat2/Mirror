"""Capability descriptors for the diff capability."""

from mirror_core.registry import CapabilityConfig

from .models import DiffRequest, DiffResult
from .protocol import Diff
from .settings import DiffSettings

capability = CapabilityConfig(
    name="diff",
    api_version="1.0.0",
    protocol=Diff,
    request_model=DiffRequest,
    result_model=DiffResult,
    settings_model=DiffSettings,
    runner="mirror_diff.runner:diff_step",
    metadata={"summary": "Diff capability"},
)
