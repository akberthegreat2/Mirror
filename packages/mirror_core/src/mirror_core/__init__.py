"""Mirror Core Kernel — capability-agnostic chassis.

This package provides the engine that powers Mirror. It knows nothing
about HTTP, parsing, archives, or any domain-specific concept.
"""

from mirror_core.application import Application
from mirror_core.components import ComponentManager
from mirror_core.discovery import DiscoveryResult, discover
from mirror_core.exceptions import (
    ApplicationError,
    ConfigurationError,
    DiscoveryError,
    LifecycleError,
    MirrorError,
    RegistryError,
    ValidationError,
)
from mirror_core.executor import (
    ExecutionResult,
    ExecutionRun,
    Executor,
    RunOutcome,
    StepState,
)
from mirror_core.lifecycle import AsyncLifecycle
from mirror_core.middleware import (
    Invocation,
    Middleware,
    MiddlewareChain,
    MiddlewareContext,
    MiddlewareInvocation,
)
from mirror_core.pipeline import ErrorPolicy, Pipeline, RetryPolicy, Step
from mirror_core.planner import CompiledStep, ExecutionPlan, Planner
from mirror_core.registry import Registry
from mirror_core.resource import BlobReference, ProducerRef, ResourceEnvelope
from mirror_core.scheduler import (
    InMemoryScheduler,
    SchedulerBackend,
    ScheduleRecord,
    ScheduleState,
    SQLiteScheduler,
)
from mirror_core.settings import MirrorSettings
from mirror_core.signals import SignalBus
from mirror_core.storage import (
    BlobStore,
    FileSystemBlobStore,
    InMemoryBlobStore,
    InMemoryMetadataStore,
    MetadataRecord,
    MetadataStore,
    SQLiteMetadataStore,
)
from mirror_core.workers import (
    ArtifactStore,
    CheckpointStore,
    ExecutionRecord,
    ExecutionStore,
    InlineWorker,
    InMemoryArtifactStore,
    InMemoryCheckpointStore,
    InMemoryExecutionStore,
    InMemoryLeaseManager,
    JobState,
    LeaseManager,
    SQLiteWorkerBackend,
    WorkerBackend,
    WorkerJob,
    WorkerLease,
)

# Note: __all__ is sorted alphabetically within each logical group.
__all__ = [
    # Exceptions
    "ApplicationError",
    "ConfigurationError",
    "DiscoveryError",
    "LifecycleError",
    "MirrorError",
    "RegistryError",
    "ValidationError",
    # Lifecycle
    "AsyncLifecycle",
    # Settings
    "MirrorSettings",
    # Discovery
    "DiscoveryResult",
    "discover",
    # Registry
    "Registry",
    # Signals
    "SignalBus",
    # Middleware
    "Invocation",
    "Middleware",
    "MiddlewareChain",
    "MiddlewareContext",
    "MiddlewareInvocation",
    # Resource
    "BlobReference",
    "ProducerRef",
    "ResourceEnvelope",
    # Storage
    "BlobStore",
    "FileSystemBlobStore",
    "InMemoryBlobStore",
    "InMemoryMetadataStore",
    "MetadataRecord",
    "MetadataStore",
    "SQLiteMetadataStore",
    # Scheduler
    "InMemoryScheduler",
    "SchedulerBackend",
    "ScheduleRecord",
    "ScheduleState",
    "SQLiteScheduler",
    # Workers
    "ArtifactStore",
    "CheckpointStore",
    "ExecutionRecord",
    "ExecutionStore",
    "InlineWorker",
    "InMemoryArtifactStore",
    "InMemoryCheckpointStore",
    "InMemoryExecutionStore",
    "InMemoryLeaseManager",
    "JobState",
    "LeaseManager",
    "SQLiteWorkerBackend",
    "WorkerBackend",
    "WorkerJob",
    "WorkerLease",
    # Pipeline
    "ErrorPolicy",
    "Pipeline",
    "RetryPolicy",
    "Step",
    # Planner
    "CompiledStep",
    "ExecutionPlan",
    "Planner",
    # Executor
    "ExecutionResult",
    "ExecutionRun",
    "Executor",
    "RunOutcome",
    "StepState",
    # Application
    "Application",
    "ComponentManager",
]