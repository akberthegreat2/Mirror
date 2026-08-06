"""Django models for Mirror Control Panel metadata and audit."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone

User = get_user_model()


class AuditModel(models.Model):
    """Abstract base model with audit fields for all Mirror models."""

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        help_text="User who created this record",
    )
    modified_at = models.DateTimeField(auto_now=True, db_index=True)
    modified_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        help_text="User who last modified this record",
    )

    class Meta:
        """Meta options for AuditModel."""

        abstract = True

    def save(
        self,
        force_insert: bool = False,
        force_update: bool = False,
        using: Optional[str] = None,
        update_fields: Optional[list[str]] = None,
    ) -> None:
        """Save with automatic modified_at update."""
        self.modified_at = timezone.now()
        super().save(force_insert, force_update, using, update_fields)


class Project(AuditModel):
    """Represents a Mirror project - a logical container for crawls and schedules."""

    name = models.CharField(max_length=255, unique=True, db_index=True)
    slug = models.SlugField(max_length=255, unique=True, db_index=True, blank=True)
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="owned_projects",
        help_text="User or team owning this project",
    )
    description = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True, db_index=True)
    metadata = models.JSONField(default=dict, blank=True, help_text="Arbitrary project metadata")

    class Meta:
        """Meta options for Project."""

        db_table = "mirror_projects"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["name", "owner"]),
            models.Index(fields=["owner", "is_active"]),
        ]
        permissions = [
            ("view_all_projects", "Can view all projects"),
            ("delete_any_project", "Can delete any project"),
        ]

    def __str__(self) -> str:
        """Human-readable representation."""
        return f"{self.name} (owner: {self.owner.username})"

    def save(
        self,
        force_insert: bool = False,
        force_update: bool = False,
        using: Optional[str] = None,
        update_fields: Optional[list[str]] = None,
    ) -> None:
        """Save with automatic slug generation if not provided."""
        if not self.slug:
            from django.utils.text import slugify

            self.slug = slugify(self.name)
        super().save(force_insert, force_update, using, update_fields)


class CrawlJob(AuditModel):
    """Represents a crawl request and tracks its execution."""

    class Status(models.TextChoices):
        """Possible crawl statuses."""

        PENDING = "pending", "Pending"
        RUNNING = "running", "Running"
        SUCCEEDED = "succeeded", "Succeeded"
        FAILED = "failed", "Failed"
        CANCELLED = "cancelled", "Cancelled"

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="crawl_jobs",
        db_index=True,
    )
    url = models.URLField(max_length=2048, db_index=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    execution_id = models.CharField(
        max_length=255,
        unique=True,
        null=True,
        blank=True,
        db_index=True,
        help_text="Mirror execution ID for tracking",
    )
    depth = models.PositiveIntegerField(
        default=1,
        help_text="Maximum crawl depth",
    )
    max_urls = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Maximum URLs to crawl",
    )
    error_message = models.TextField(blank=True, default="")
    started_at = models.DateTimeField(null=True, blank=True, db_index=True)
    completed_at = models.DateTimeField(null=True, blank=True, db_index=True)

    class Meta:
        """Meta options for CrawlJob."""

        db_table = "mirror_crawl_jobs"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["project", "status"]),
            models.Index(fields=["execution_id"]),
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["project", "created_at"]),
        ]
        permissions = [
            ("retry_crawl", "Can retry failed crawls"),
            ("cancel_crawl", "Can cancel running crawls"),
            ("view_all_crawls", "Can view all crawls regardless of project"),
        ]

    def __str__(self) -> str:
        """Human-readable representation."""
        return f"Crawl {self.url} ({self.status})"

    def mark_started(self) -> None:
        """Mark crawl as started."""
        self.status = self.Status.RUNNING
        self.started_at = timezone.now()
        self.save(update_fields=["status", "started_at"])

    def mark_completed(
        self,
        success: bool,
        error: Optional[str] = None,
    ) -> None:
        """Mark crawl as completed.

        Args:
            success: Whether the crawl succeeded.
            error: Optional error message if failed.
        """
        self.status = self.Status.SUCCEEDED if success else self.Status.FAILED
        self.completed_at = timezone.now()
        if error:
            self.error_message = error
        self.save(update_fields=["status", "completed_at", "error_message"])

    def mark_cancelled(self) -> None:
        """Mark crawl as cancelled."""
        self.status = self.Status.CANCELLED
        self.completed_at = timezone.now()
        self.save(update_fields=["status", "completed_at"])

    def retry(self) -> None:
        """Reset crawl for retry."""
        if self.status in [self.Status.FAILED, self.Status.CANCELLED]:
            self.status = self.Status.PENDING
            self.completed_at = None
            self.error_message = ""
            self.save(update_fields=["status", "completed_at", "error_message"])

    def can_retry(self) -> bool:
        """Check if crawl can be retried."""
        return self.status in [self.Status.FAILED, self.Status.CANCELLED]

    def can_cancel(self) -> bool:
        """Check if crawl can be cancelled."""
        return self.status == self.Status.RUNNING


class CrawledURL(AuditModel):
    """Represents a discovered URL during crawling.

    Important: This solves the legacy Mirror problem where crawled results
    were not persisted. Every discovered URL is stored here.
    """

    crawl = models.ForeignKey(
        CrawlJob,
        on_delete=models.CASCADE,
        related_name="discovered_urls",
        db_index=True,
    )
    url = models.URLField(max_length=2048, db_index=True)
    depth = models.PositiveIntegerField(default=0)
    status_code = models.PositiveIntegerField(null=True, blank=True)
    title = models.CharField(max_length=500, blank=True, default="")
    content_type = models.CharField(max_length=255, blank=True, default="")
    discovered_at = models.DateTimeField(auto_now_add=True, db_index=True)
    crawled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        """Meta options for CrawledURL."""

        db_table = "mirror_crawled_urls"
        ordering = ["-discovered_at"]
        unique_together = [["crawl", "url"]]
        indexes = [
            models.Index(fields=["crawl", "url"]),
            models.Index(fields=["url"]),
            models.Index(fields=["discovered_at"]),
            models.Index(fields=["crawl", "discovered_at"]),
        ]

    def __str__(self) -> str:
        """Human-readable representation."""
        return f"{self.url} (depth {self.depth})"


class ArchiveRecord(AuditModel):
    """Metadata for archived content.

    Database stores metadata only. Actual blob storage (filesystem, S3, etc.)
    is handled by Mirror's storage layer.
    """

    class Format(models.TextChoices):
        """Archive format types."""

        WARC = "warc", "WARC"
        JSON = "json", "JSON"
        HTML = "html", "HTML"
        PDF = "pdf", "PDF"
        PNG = "png", "PNG"
        JPEG = "jpeg", "JPEG"
        OTHER = "other", "Other"

    crawl = models.ForeignKey(
        CrawlJob,
        on_delete=models.CASCADE,
        related_name="archive_records",
        db_index=True,
    )
    url = models.URLField(max_length=2048, db_index=True)
    blob_key = models.CharField(
        max_length=1024,
        db_index=True,
        help_text="Key/path in blob storage",
    )
    format = models.CharField(
        max_length=20,
        choices=Format.choices,
        default=Format.WARC,
        db_index=True,
    )
    size = models.PositiveBigIntegerField(
        null=True,
        blank=True,
        help_text="Size in bytes",
    )
    checksum = models.CharField(
        max_length=128,
        blank=True,
        default="",
        help_text="SHA-256 checksum",
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional archive metadata",
    )

    class Meta:
        """Meta options for ArchiveRecord."""

        db_table = "mirror_archive_records"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["crawl", "url"]),
            models.Index(fields=["blob_key"]),
            models.Index(fields=["format"]),
            models.Index(fields=["crawl", "format"]),
        ]
        permissions = [
            ("view_all_archives", "Can view all archive records"),
        ]

    def __str__(self) -> str:
        """Human-readable representation."""
        return f"Archive {self.blob_key} ({self.format})"


class Worker(AuditModel):
    """Represents a Mirror worker instance."""

    class Status(models.TextChoices):
        """Worker status options."""

        ONLINE = "online", "Online"
        OFFLINE = "offline", "Offline"
        BUSY = "busy", "Busy"
        DRAINING = "draining", "Draining"

    name = models.CharField(max_length=255, unique=True, db_index=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.OFFLINE,
        db_index=True,
    )
    current_job = models.ForeignKey(
        CrawlJob,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_workers",
        db_index=True,
    )
    capabilities = models.JSONField(
        default=list,
        blank=True,
        help_text="List of capability names this worker supports",
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional worker metadata",
    )
    last_seen = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Last heartbeat received",
    )

    class Meta:
        """Meta options for Worker."""

        db_table = "mirror_workers"
        ordering = ["-last_seen"]
        indexes = [
            models.Index(fields=["status", "last_seen"]),
            models.Index(fields=["current_job"]),
            models.Index(fields=["name", "last_seen"]),
        ]
        permissions = [
            ("force_worker_offline", "Can force workers offline"),
            ("view_all_workers", "Can view all workers"),
        ]

    def __str__(self) -> str:
        """Human-readable representation."""
        status_display = self.get_status_display()
        return f"{self.name} ({status_display})"

    def heartbeat(self) -> None:
        """Update worker heartbeat."""
        self.last_seen = timezone.now()
        self.save(update_fields=["last_seen"])

    def set_status(self, status: str) -> None:
        """Set worker status."""
        self.status = status
        self.save(update_fields=["status"])

    def is_online(self) -> bool:
        """Check if worker is online.

        Worker is considered online if:
        - Status is not OFFLINE
        - Last heartbeat was within 60 seconds
        """
        if self.status == self.Status.OFFLINE:
            return False
        if self.last_seen:
            delta = timezone.now() - self.last_seen
            return delta.total_seconds() < 60
        return False


class Schedule(AuditModel):
    """Represents a scheduled crawl job."""

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="schedules",
        db_index=True,
    )
    name = models.CharField(max_length=255, db_index=True)
    url = models.URLField(max_length=2048)
    cron_expression = models.CharField(
        max_length=100,
        help_text="Cron expression for scheduling (e.g., '0 2 * * *')",
    )
    depth = models.PositiveIntegerField(default=1)
    max_urls = models.PositiveIntegerField(null=True, blank=True)
    enabled = models.BooleanField(default=True, db_index=True)
    metadata = models.JSONField(default=dict, blank=True)
    last_run = models.DateTimeField(null=True, blank=True, db_index=True)
    next_run = models.DateTimeField(null=True, blank=True, db_index=True)

    class Meta:
        """Meta options for Schedule."""

        db_table = "mirror_schedules"
        ordering = ["-created_at"]
        unique_together = [["project", "name"]]
        indexes = [
            models.Index(fields=["project", "enabled"]),
            models.Index(fields=["next_run"]),
            models.Index(fields=["project", "next_run"]),
        ]
        permissions = [
            ("view_all_schedules", "Can view all schedules"),
        ]

    def __str__(self) -> str:
        """Human-readable representation."""
        status = "enabled" if self.enabled else "disabled"
        return f"{self.name} ({self.cron_expression}) - {status}"

    def enable(self) -> None:
        """Enable this schedule."""
        self.enabled = True
        self.save(update_fields=["enabled"])

    def disable(self) -> None:
        """Disable this schedule."""
        self.enabled = False
        self.save(update_fields=["enabled"])

    def mark_run(self) -> None:
        """Mark schedule as run and calculate next run."""
        self.last_run = timezone.now()
        # Calculate next run using croniter
        try:
            from croniter import croniter

            iterator = croniter(self.cron_expression, self.last_run)
            self.next_run = iterator.get_next(datetime)
        except ImportError:
            # Fallback: don't set next_run if croniter not installed
            pass
        self.save(update_fields=["last_run", "next_run"])


class AuditLog(models.Model):
    """Immutable audit log for all Mirror operations.

    This is separate from AuditModel because it's append-only and immutable.
    """

    class Action(models.TextChoices):
        """Audit action types."""

        CREATE = "create", "Create"
        UPDATE = "update", "Update"
        DELETE = "delete", "Delete"
        START = "start", "Start"
        RETRY = "retry", "Retry"
        CANCEL = "cancel", "Cancel"
        LOGIN = "login", "Login"
        LOGOUT = "logout", "Logout"
        FAIL = "fail", "Fail"
        COMPLETE = "complete", "Complete"

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
        db_index=True,
    )
    action = models.CharField(
        max_length=20,
        choices=Action.choices,
        db_index=True,
    )
    resource_type = models.CharField(
        max_length=100,
        db_index=True,
        help_text="Model name (e.g., 'CrawlJob', 'Project')",
    )
    resource_id = models.CharField(
        max_length=100,
        db_index=True,
        help_text="String representation of resource ID",
    )
    changes = models.JSONField(
        default=dict,
        blank=True,
        help_text="Record of what changed",
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True, default="")
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        """Meta options for AuditLog."""

        db_table = "mirror_audit_logs"
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["timestamp"]),
            models.Index(fields=["user", "timestamp"]),
            models.Index(fields=["resource_type", "resource_id"]),
            models.Index(fields=["action", "timestamp"]),
        ]
        # Audit logs are immutable - no updates or deletes
        permissions = [
            ("view_audit_logs", "Can view audit logs"),
        ]

    def __str__(self) -> str:
        """Human-readable representation."""
        user_str = self.user.username if self.user else "system"
        return (
            f"{user_str} {self.action} {self.resource_type} {self.resource_id} at {self.timestamp}"
        )

    def save(
        self,
        force_insert: bool = False,
        force_update: bool = False,
        using: Optional[str] = None,
        update_fields: Optional[list[str]] = None,
    ) -> None:
        """Override save to enforce immutability.

        Audit logs are append-only. Updates are not allowed.
        """
        if self.pk:
            raise RuntimeError("AuditLog entries are immutable and cannot be updated")
        super().save(force_insert, force_update, using, update_fields)

    def delete(self) -> None:
        """Override delete to enforce immutability.

        Audit logs are append-only. Deletions are not allowed.
        """
        raise RuntimeError("AuditLog entries are immutable and cannot be deleted")
