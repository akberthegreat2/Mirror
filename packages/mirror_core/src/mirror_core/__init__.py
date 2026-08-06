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

__all__ = [
    "Application",
    "ApplicationError",
    "ArtifactStore",
    "AsyncLifecycle",
    "BlobReference",
    "BlobStore",
    "CheckpointStore",
    "CompiledStep",
    "ComponentManager",
    "ConfigurationError",
    "DiscoveryError",
    "DiscoveryResult",
    "ErrorPolicy",
    "ExecutionPlan",
    "ExecutionRecord",
    "ExecutionResult",
    "ExecutionRun",
    "ExecutionStore",
    "Executor",
    "FileSystemBlobStore",
    "InMemoryArtifactStore",
    "InMemoryBlobStore",
    "InMemoryCheckpointStore",
    "InMemoryExecutionStore",
    "InMemoryLeaseManager",
    "InMemoryMetadataStore",
    "InMemoryScheduler",
    "InlineWorker",
    "Invocation",
    "JobState",
    "LeaseManager",
    "LifecycleError",
    "MetadataRecord",
    "MetadataStore",
    "Middleware",
    "MiddlewareChain",
    "MiddlewareContext",
    "MiddlewareInvocation",
    "MirrorError",
    "MirrorSettings",
    "Pipeline",
    "Planner",
    "ProducerRef",
    "Registry",
    "RegistryError",
    "ResourceEnvelope",
    "RetryPolicy",
    "RunOutcome",
    "SQLiteMetadataStore",
    "SQLiteScheduler",
    "SQLiteWorkerBackend",
    "ScheduleRecord",
    "ScheduleState",
    "SchedulerBackend",
    "SignalBus",
    "Step",
    "StepState",
    "ValidationError",
    "WorkerBackend",
    "WorkerJob",
    "WorkerLease",
    "discover",
]
