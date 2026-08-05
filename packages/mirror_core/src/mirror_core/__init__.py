"""Mirror Core Kernel — capability-agnostic chassis.

This package provides the engine that powers Mirror. It knows nothing
about HTTP, parsing, archives, or any domain-specific concept.
"""

from mirror_core.application import Application
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
from mirror_core.middleware import Invocation, Middleware, MiddlewareChain
from mirror_core.pipeline import ErrorPolicy, Pipeline, RetryPolicy, Step
from mirror_core.planner import CompiledStep, ExecutionPlan, Planner
from mirror_core.registry import Registry
from mirror_core.resource import BlobReference, ProducerRef, ResourceEnvelope
from mirror_core.scheduler import (
    InMemoryScheduler,
    SQLiteScheduler,
    ScheduleRecord,
    ScheduleState,
    SchedulerBackend,
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
    InMemoryArtifactStore,
    InMemoryCheckpointStore,
    InMemoryExecutionStore,
    InMemoryLeaseManager,
    InlineWorker,
    JobState,
    LeaseManager,
    SQLiteWorkerBackend,
    WorkerBackend,
    WorkerJob,
    WorkerLease,
)

__all__ = [
    # Exceptions
    "MirrorError",
    "ConfigurationError",
    "LifecycleError",
    "ApplicationError",
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
    # Storage
    "MetadataRecord",
    "MetadataStore",
    "BlobStore",
    "InMemoryMetadataStore",
    "InMemoryBlobStore",
    "SQLiteMetadataStore",
    "FileSystemBlobStore",
    # Workers
    "JobState",
    "WorkerJob",
    "WorkerLease",
    "ExecutionRecord",
    "WorkerBackend",
    "ExecutionStore",
    "CheckpointStore",
    "ArtifactStore",
    "LeaseManager",
    "InlineWorker",
    "SQLiteWorkerBackend",
    "InMemoryExecutionStore",
    "InMemoryCheckpointStore",
    "InMemoryArtifactStore",
    "InMemoryLeaseManager",
    # Scheduler
    "ScheduleState",
    "ScheduleRecord",
    "SchedulerBackend",
    "InMemoryScheduler",
    "SQLiteScheduler",
    # Middleware
    "Invocation",
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
    "CompiledStep",
    "ExecutionPlan",
    # Executor
    "Executor",
    "ExecutionRun",
    "ExecutionResult",
    "RunOutcome",
    "StepState",
    # Application
    "Application",
]
