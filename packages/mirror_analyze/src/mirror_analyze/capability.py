"""Capability descriptors for the analyze capability."""

from mirror_core.registry import CapabilityConfig

from .models import AnalyzeRequest, AnalyzeResult
from .protocol import Analyze
from .settings import AnalyzeSettings

capability = CapabilityConfig(
    name="analyze",
    api_version="1.0.0",
    protocol=Analyze,
    request_model=AnalyzeRequest,
    result_model=AnalyzeResult,
    settings_model=AnalyzeSettings,
    runner="mirror_analyze.runner:analyze_step",
    metadata={"summary": "Analyze capability"},
)
