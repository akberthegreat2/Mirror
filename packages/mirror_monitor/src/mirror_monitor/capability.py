"""Capability descriptors for the monitor capability."""

from mirror_core.registry import CapabilityConfig

from .models import MonitorRequest, MonitorResult
from .protocol import Monitor
from .settings import MonitorSettings

capability = CapabilityConfig(
    name="monitor",
    api_version="1.0.0",
    protocol=Monitor,
    request_model=MonitorRequest,
    result_model=MonitorResult,
    settings_model=MonitorSettings,
    runner="mirror_monitor.runner:monitor_step",
    metadata={"summary": "Monitor capability"},
)
