"""Mirror Core Kernel — capability-agnostic chassis.

This package provides the engine that powers Mirror. It knows nothing
about HTTP, parsing, archives, or any domain-specific concept.
"""

from mirror_core.exceptions import (
    MirrorError,
    ConfigurationError,
    LifecycleError,
    DiscoveryError,
    RegistryError,
    ValidationError,
)
from mirror_core.lifecycle import AsyncLifecycle
from mirror_core.settings import MirrorSettings
from mirror_core.discovery import discover, DiscoveryResult
from mirror_core.registry import Registry
from mirror_core.signals import SignalBus
from mirror_core.middleware import Middleware, MiddlewareChain
from mirror_core.resource import ResourceEnvelope, ProducerRef, BlobReference
from mirror_core.pipeline import Step, Pipeline, RetryPolicy, ErrorPolicy
from mirror_core.planner import Planner, ExecutionPlan
from mirror_core.executor import Executor, StepState
from mirror_core.application import Application

__all__ = [
    # Exceptions
    "MirrorError",
    "ConfigurationError",
    "LifecycleError",
    "DiscoveryError",
    "RegistryError",
    "ValidationError",
    # Lifecycle
    "AsyncLifecycle",
    # Settings
    "MirrorSettings",
    # Discovery
    "discover",
    "DiscoveryResult",
    # Registry
    "Registry",
    # Signals
    "SignalBus",
    # Middleware
    "Middleware",
    "MiddlewareChain",
    # Resource
    "ResourceEnvelope",
    "ProducerRef",
    "BlobReference",
    # Pipeline
    "Step",
    "Pipeline",
    "RetryPolicy",
    "ErrorPolicy",
    # Planner
    "Planner",
    "ExecutionPlan",
    # Executor
    "Executor",
    "StepState",
    # Application
    "Application",
]