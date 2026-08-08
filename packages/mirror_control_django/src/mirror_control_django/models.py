"""Django models for Mirror's control plane."""

from __future__ import annotations

from typing import ClassVar
from uuid import uuid4

from django.db import models


class TimestampedModel(models.Model):
    """Abstract base model with creation and update timestamps."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Project(TimestampedModel):
    """Mirror application workspace."""

    slug = models.SlugField(unique=True, max_length=120)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering: ClassVar[list[str]] = ["slug"]

    def __str__(self) -> str:
        return self.name


class Pipeline(TimestampedModel):
    """Named pipeline definition and governance record."""

    class Origin(models.TextChoices):
        CODE = "code", "Code"
        MANAGED = "managed", "Managed"

    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="pipelines"
    )
    slug = models.SlugField(max_length=120)
    name = models.CharField(max_length=200)
    origin = models.CharField(
        max_length=20, choices=Origin.choices, default=Origin.MANAGED
    )
    is_read_only = models.BooleanField(default=False)
    source_ref = models.CharField(max_length=500, blank=True)
    source_hash = models.CharField(max_length=128, blank=True)
    definition_ref = models.CharField(max_length=500, blank=True)
    current_version_number = models.PositiveIntegerField(default=1)
    current_version_hash = models.CharField(max_length=128, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering: ClassVar[list[str]] = ["project__slug", "slug"]
        constraints: ClassVar[list[models.UniqueConstraint]] = [
            models.UniqueConstraint(
                fields=("project", "slug"), name="uniq_mirror_control_pipeline_slug"
            )
        ]

    def __str__(self) -> str:
        return f"{self.project.slug}:{self.slug}"


class PipelineVersion(TimestampedModel):
    """Immutable version snapshot of a pipeline definition."""

    pipeline = models.ForeignKey(
        Pipeline, on_delete=models.CASCADE, related_name="versions"
    )
    version = models.PositiveIntegerField()
    definition_ref = models.CharField(max_length=500)
    definition_hash = models.CharField(max_length=128)
    definition_format = models.CharField(max_length=20, default="json")
    notes = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering: ClassVar[list[str]] = [
            "pipeline__project__slug",
            "pipeline__slug",
            "version",
        ]
        constraints: ClassVar[list[models.UniqueConstraint]] = [
            models.UniqueConstraint(
                fields=("pipeline", "version"),
                name="uniq_mirror_control_pipeline_version",
            )
        ]

    def __str__(self) -> str:
        return f"{self.pipeline.slug}@v{self.version}"


class ExecutionRun(TimestampedModel):
    """One execution of a pipeline or one-shot operation."""

    class Status(models.TextChoices):
        QUEUED = "queued", "Queued"
        RUNNING = "running", "Running"
        SUCCEEDED = "succeeded", "Succeeded"
        FAILED = "failed", "Failed"
        CANCELLED = "cancelled", "Cancelled"

    run_id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    pipeline = models.ForeignKey(
        Pipeline, null=True, blank=True, on_delete=models.SET_NULL, related_name="runs"
    )
    pipeline_name = models.CharField(max_length=200, blank=True)
    pipeline_version = models.PositiveIntegerField(null=True, blank=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.QUEUED
    )
    execution_class = models.CharField(max_length=40, default="default")
    worker_id = models.CharField(max_length=120, blank=True)
    queue_name = models.CharField(max_length=120, blank=True)
    input_payload = models.JSONField(default=dict, blank=True)
    result_payload = models.JSONField(default=dict, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering: ClassVar[list[str]] = ["-created_at", "run_id"]

    def __str__(self) -> str:
        return str(self.run_id)


class ExecutionStep(TimestampedModel):
    """One step inside an execution run."""

    class Status(models.TextChoices):
        QUEUED = "queued", "Queued"
        RUNNING = "running", "Running"
        SUCCEEDED = "succeeded", "Succeeded"
        FAILED = "failed", "Failed"
        SKIPPED = "skipped", "Skipped"

    run = models.ForeignKey(
        ExecutionRun, on_delete=models.CASCADE, related_name="steps"
    )
    step_id = models.CharField(max_length=200)
    capability = models.CharField(max_length=200)
    provider = models.CharField(max_length=200, blank=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.QUEUED
    )
    input_payload = models.JSONField(default=dict, blank=True)
    output_payload = models.JSONField(default=dict, blank=True)
    error_text = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering: ClassVar[list[str]] = ["run__created_at", "run_id", "step_id"]
        constraints: ClassVar[list[models.UniqueConstraint]] = [
            models.UniqueConstraint(
                fields=("run", "step_id"), name="uniq_mirror_control_execution_step"
            )
        ]

    def __str__(self) -> str:
        return f"{self.run_id}:{self.step_id}"


class Worker(TimestampedModel):
    """Control-plane worker record or heartbeat projection."""

    class Status(models.TextChoices):
        ONLINE = "online", "Online"
        OFFLINE = "offline", "Offline"
        DEGRADED = "degraded", "Degraded"

    worker_id = models.CharField(primary_key=True, max_length=120)
    backend = models.CharField(max_length=120, blank=True)
    execution_class = models.CharField(max_length=40, default="default")
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.OFFLINE
    )
    heartbeat_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering: ClassVar[list[str]] = ["worker_id"]

    def __str__(self) -> str:
        return self.worker_id


class Schedule(TimestampedModel):
    """Scheduled execution policy for a pipeline."""

    pipeline = models.ForeignKey(
        Pipeline, on_delete=models.CASCADE, related_name="schedules"
    )
    name = models.CharField(max_length=200)
    cron = models.CharField(max_length=200)
    timezone_name = models.CharField(max_length=64, default="UTC")
    enabled = models.BooleanField(default=True)
    next_run_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering: ClassVar[list[str]] = ["name"]
        constraints: ClassVar[list[models.UniqueConstraint]] = [
            models.UniqueConstraint(
                fields=("pipeline", "name"), name="uniq_mirror_control_schedule"
            )
        ]

    def __str__(self) -> str:
        return self.name


class CrawledURL(TimestampedModel):
    """URL discovered or crawled by the Crawl capability."""

    class Status(models.TextChoices):
        DISCOVERED = "discovered", "Discovered"
        FETCHED = "fetched", "Fetched"
        FAILED = "failed", "Failed"

    url = models.URLField(max_length=2048)
    project = models.ForeignKey(
        Project,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="crawled_urls",
    )
    pipeline = models.ForeignKey(
        Pipeline,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="crawled_urls",
    )
    run_id = models.UUIDField(null=True, blank=True, db_index=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.DISCOVERED
    )
    discovered_at = models.DateTimeField(auto_now_add=True)
    fetched_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering: ClassVar[list[str]] = ["-discovered_at", "url"]
        indexes: ClassVar[list[models.Index]] = [models.Index(fields=["url"])]

    def __str__(self) -> str:
        return self.url


class ArchiveRecord(TimestampedModel):
    """Archived resource reference produced by Archive."""

    pipeline = models.ForeignKey(
        Pipeline,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="archives",
    )
    run_id = models.UUIDField(null=True, blank=True, db_index=True)
    resource_key = models.CharField(max_length=500)
    storage_ref = models.CharField(max_length=500)
    mime_type = models.CharField(max_length=120, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering: ClassVar[list[str]] = ["-created_at", "resource_key"]
        indexes: ClassVar[list[models.Index]] = [models.Index(fields=["resource_key"])]

    def __str__(self) -> str:
        return self.resource_key


class Checkpoint(TimestampedModel):
    """Persisted checkpoint for resumable execution."""

    run_id = models.UUIDField(db_index=True)
    step_id = models.CharField(max_length=200)
    payload = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering: ClassVar[list[str]] = ["-created_at", "run_id", "step_id"]
        constraints: ClassVar[list[models.UniqueConstraint]] = [
            models.UniqueConstraint(
                fields=("run_id", "step_id"), name="uniq_mirror_control_checkpoint"
            )
        ]

    def __str__(self) -> str:
        return f"{self.run_id}:{self.step_id}"


class DeadLetter(TimestampedModel):
    """Terminal failure record for a run or step."""

    run_id = models.UUIDField(primary_key=True, editable=False)
    pipeline = models.ForeignKey(
        Pipeline,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="dead_letters",
    )
    pipeline_name = models.CharField(max_length=200)
    step_id = models.CharField(max_length=200, blank=True)
    reason = models.TextField()
    original_inputs = models.JSONField(default=dict, blank=True)
    policy_state = models.JSONField(default=dict, blank=True)
    provenance = models.JSONField(default=dict, blank=True)
    retry_count = models.PositiveIntegerField(default=0)
    terminal_status = models.CharField(max_length=40)
    worker_id = models.CharField(max_length=120, blank=True)
    lease_id = models.CharField(max_length=120, blank=True)

    class Meta:
        ordering: ClassVar[list[str]] = ["-created_at", "run_id"]

    def __str__(self) -> str:
        return str(self.run_id)
