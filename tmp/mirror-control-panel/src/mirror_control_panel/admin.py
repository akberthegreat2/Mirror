"""Django admin interface for Mirror Control Panel."""

from typing import Any, Optional

from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import path
from django.utils.html import format_html

from mirror_control_panel.models import (
    ArchiveRecord,
    AuditLog,
    CrawlJob,
    CrawledURL,
    Project,
    Schedule,
    Worker,
)
from mirror_control_panel.permissions import user_can_cancel_crawl, user_can_retry_crawl
from mirror_control_panel.services import CrawlService


@admin.register(Project)
class ProjectAdmin(ModelAdmin):
    """Admin interface for Project."""

    list_display = ["name", "slug", "owner", "is_active", "created_at", "updated_at"]
    list_filter = ["is_active", "created_at", "owner"]
    search_fields = ["name", "slug", "description", "owner__username"]
    readonly_fields = ["created_at", "updated_at", "created_by", "modified_by"]
    ordering = ["-created_at"]
    fieldsets = (
        (None, {"fields": ("name", "slug", "owner", "is_active")}),
        ("Description", {"fields": ("description",)}),
        (
            "Metadata",
            {
                "fields": ("metadata",),
                "classes": ("collapse",),
            },
        ),
        (
            "Audit",
            {
                "fields": ("created_at", "created_by", "updated_at", "modified_by"),
                "classes": ("collapse",),
            },
        ),
    )

    def get_queryset(self, request: HttpRequest) -> QuerySet[Project]:
        """Filter queryset based on user permissions."""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if request.user.has_perm("mirror_control_panel.view_all_projects"):
            return qs
        return qs.filter(owner=request.user)

    def has_add_permission(self, request: HttpRequest) -> bool:
        """Check if user can add projects."""
        return request.user.has_perm("mirror_control_panel.add_project")

    def has_change_permission(self, request: HttpRequest, obj: Optional[Project] = None) -> bool:
        """Check if user can change this project."""
        if request.user.is_superuser:
            return True
        if obj is None:
            return request.user.has_perm("mirror_control_panel.change_project")
        if request.user.has_perm("mirror_control_panel.view_all_projects"):
            return True
        return obj.owner == request.user

    def has_delete_permission(self, request: HttpRequest, obj: Optional[Project] = None) -> bool:
        """Check if user can delete this project."""
        if request.user.is_superuser:
            return True
        if obj is None:
            return False
        if request.user.has_perm("mirror_control_panel.delete_any_project"):
            return True
        return obj.owner == request.user

    def save_model(self, request: HttpRequest, obj: Project, form: Any, change: bool) -> None:
        """Save model with audit fields."""
        if not change:
            obj.created_by = request.user
        obj.modified_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(CrawlJob)
class CrawlJobAdmin(ModelAdmin):
    """Admin interface for CrawlJob."""

    list_display = [
        "id",
        "url",
        "project",
        "status_colored",
        "execution_id",
        "created_by",
        "created_at",
        "completed_at",
    ]
    list_filter = ["status", "created_at", "completed_at", "project"]
    search_fields = ["url", "execution_id", "error_message", "created_by__username"]
    readonly_fields = ["created_at", "started_at", "completed_at", "execution_id", "created_by"]
    ordering = ["-created_at"]
    actions = ["retry_crawls", "cancel_crawls"]
    fieldsets = (
        (None, {"fields": ("project", "url", "status", "execution_id")}),
        ("Crawl Configuration", {"fields": ("depth", "max_urls")}),
        (
            "Error Information",
            {
                "fields": ("error_message",),
                "classes": ("collapse",),
            },
        ),
        (
            "Timestamps",
            {
                "fields": ("created_at", "started_at", "completed_at"),
                "classes": ("collapse",),
            },
        ),
        (
            "Audit",
            {
                "fields": ("created_by", "modified_by"),
                "classes": ("collapse",),
            },
        ),
    )

    def status_colored(self, obj: CrawlJob) -> str:
        """Display status with color coding."""
        colors = {
            "pending": "orange",
            "running": "blue",
            "succeeded": "green",
            "failed": "red",
            "cancelled": "gray",
        }
        color = colors.get(obj.status, "black")
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display(),
        )

    status_colored.short_description = "Status"

    def get_queryset(self, request: HttpRequest) -> QuerySet[CrawlJob]:
        """Filter queryset based on user permissions."""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if request.user.has_perm("mirror_control_panel.view_all_crawls"):
            return qs
        return qs.filter(project__owner=request.user)

    def has_add_permission(self, request: HttpRequest) -> bool:
        """Check if user can add crawls."""
        return request.user.has_perm("mirror_control_panel.add_crawljob")

    def has_change_permission(self, request: HttpRequest, obj: Optional[CrawlJob] = None) -> bool:
        """Check if user can change this crawl."""
        if request.user.is_superuser:
            return True
        if obj is None:
            return request.user.has_perm("mirror_control_panel.change_crawljob")
        if request.user.has_perm("mirror_control_panel.view_all_crawls"):
            return True
        return obj.project.owner == request.user

    @admin.action(description="Retry selected crawls")
    def retry_crawls(self, request: HttpRequest, queryset: QuerySet[CrawlJob]) -> None:
        """Retry failed or cancelled crawls."""
        service = CrawlService()
        count = 0
        for crawl in queryset:
            if crawl.can_retry() and user_can_retry_crawl(request.user, crawl):
                service.retry_crawl(crawl.id, request.user)
                count += 1
        self.message_user(request, f"Retried {count} crawl(s).")

    @admin.action(description="Cancel selected crawls")
    def cancel_crawls(self, request: HttpRequest, queryset: QuerySet[CrawlJob]) -> None:
        """Cancel running crawls."""
        service = CrawlService()
        count = 0
        for crawl in queryset:
            if crawl.can_cancel() and user_can_cancel_crawl(request.user, crawl):
                service.cancel_crawl(crawl.id, request.user)
                count += 1
        self.message_user(request, f"Cancelled {count} crawl(s).")

    def get_urls(self) -> list[path]:
        """Add custom admin URLs."""
        urls = super().get_urls()
        custom_urls = [
            path(
                "<int:crawl_id>/retry/",
                self.admin_site.admin_view(self.retry_crawl_view),
                name="crawljob_retry",
            ),
            path(
                "<int:crawl_id>/cancel/",
                self.admin_site.admin_view(self.cancel_crawl_view),
                name="crawljob_cancel",
            ),
        ]
        return custom_urls + urls

    def retry_crawl_view(self, request: HttpRequest, crawl_id: int) -> HttpResponse:
        """Custom view to retry a single crawl."""
        crawl = get_object_or_404(CrawlJob, id=crawl_id)
        if crawl.can_retry() and user_can_retry_crawl(request.user, crawl):
            service = CrawlService()
            service.retry_crawl(crawl.id, request.user)
            self.message_user(request, f"Crawl {crawl.id} retried successfully.")
        return redirect("admin:mirror_control_panel_crawljob_changelist")

    def cancel_crawl_view(self, request: HttpRequest, crawl_id: int) -> HttpResponse:
        """Custom view to cancel a single crawl."""
        crawl = get_object_or_404(CrawlJob, id=crawl_id)
        if crawl.can_cancel() and user_can_cancel_crawl(request.user, crawl):
            service = CrawlService()
            service.cancel_crawl(crawl.id, request.user)
            self.message_user(request, f"Crawl {crawl.id} cancelled successfully.")
        return redirect("admin:mirror_control_panel_crawljob_changelist")

    def save_model(self, request: HttpRequest, obj: CrawlJob, form: Any, change: bool) -> None:
        """Save model with audit fields."""
        if not change:
            obj.created_by = request.user
        obj.modified_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(CrawledURL)
class CrawledURLAdmin(ModelAdmin):
    """Admin interface for CrawledURL."""

    list_display = [
        "url",
        "crawl",
        "depth",
        "status_code",
        "content_type",
        "discovered_at",
        "created_by",
    ]
    list_filter = ["depth", "status_code", "content_type", "discovered_at"]
    search_fields = ["url", "title"]
    readonly_fields = ["discovered_at", "created_at", "created_by"]
    ordering = ["-discovered_at"]
    fieldsets = (
        (None, {"fields": ("crawl", "url", "depth")}),
        ("Response Information", {"fields": ("status_code", "content_type", "title")}),
        (
            "Timestamps",
            {
                "fields": ("discovered_at", "crawled_at"),
                "classes": ("collapse",),
            },
        ),
        (
            "Audit",
            {
                "fields": ("created_at", "created_by"),
                "classes": ("collapse",),
            },
        ),
    )

    def get_queryset(self, request: HttpRequest) -> QuerySet[CrawledURL]:
        """Filter queryset based on user permissions."""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if request.user.has_perm("mirror_control_panel.view_all_crawls"):
            return qs
        return qs.filter(crawl__project__owner=request.user)

    def has_add_permission(self, request: HttpRequest) -> bool:
        """Check if user can add crawled URLs."""
        return request.user.has_perm("mirror_control_panel.add_crawledurl")

    def save_model(self, request: HttpRequest, obj: CrawledURL, form: Any, change: bool) -> None:
        """Save model with audit fields."""
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(ArchiveRecord)
class ArchiveRecordAdmin(ModelAdmin):
    """Admin interface for ArchiveRecord."""

    list_display = [
        "id",
        "url",
        "crawl",
        "format",
        "size_display",
        "blob_key_short",
        "created_at",
        "created_by",
    ]
    list_filter = ["format", "created_at", "crawl"]
    search_fields = ["url", "blob_key", "checksum"]
    readonly_fields = ["created_at", "created_by"]
    ordering = ["-created_at"]
    fieldsets = (
        (None, {"fields": ("crawl", "url", "blob_key", "format")}),
        ("File Information", {"fields": ("size", "checksum")}),
        (
            "Metadata",
            {
                "fields": ("metadata",),
                "classes": ("collapse",),
            },
        ),
        (
            "Timestamps",
            {
                "fields": ("created_at",),
                "classes": ("collapse",),
            },
        ),
        (
            "Audit",
            {
                "fields": ("created_by",),
                "classes": ("collapse",),
            },
        ),
    )

    def size_display(self, obj: ArchiveRecord) -> str:
        """Display size in human-readable format."""
        if obj.size is None:
            return "-"
        for unit in ["B", "KB", "MB", "GB"]:
            if obj.size < 1024:
                return f"{obj.size:.1f} {unit}"
            obj.size /= 1024
        return f"{obj.size:.1f} TB"

    size_display.short_description = "Size"

    def blob_key_short(self, obj: ArchiveRecord) -> str:
        """Display shortened blob key."""
        if len(obj.blob_key) > 50:
            return f"{obj.blob_key[:47]}..."
        return obj.blob_key

    blob_key_short.short_description = "Blob Key"

    def get_queryset(self, request: HttpRequest) -> QuerySet[ArchiveRecord]:
        """Filter queryset based on user permissions."""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if request.user.has_perm("mirror_control_panel.view_all_archives"):
            return qs
        return qs.filter(crawl__project__owner=request.user)

    def has_add_permission(self, request: HttpRequest) -> bool:
        """Check if user can add archive records."""
        return request.user.has_perm("mirror_control_panel.add_archiverecord")

    def save_model(self, request: HttpRequest, obj: ArchiveRecord, form: Any, change: bool) -> None:
        """Save model with audit fields."""
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Worker)
class WorkerAdmin(ModelAdmin):
    """Admin interface for Worker."""

    list_display = [
        "name",
        "status_colored",
        "current_job",
        "last_seen",
        "is_online_display",
        "created_at",
    ]
    list_filter = ["status", "created_at"]
    search_fields = ["name", "current_job__url"]
    readonly_fields = ["created_at", "updated_at", "created_by", "modified_by"]
    ordering = ["-last_seen"]
    actions = ["force_offline"]
    fieldsets = (
        (None, {"fields": ("name", "status", "current_job")}),
        ("Capabilities", {"fields": ("capabilities",)}),
        (
            "Metadata",
            {
                "fields": ("metadata",),
                "classes": ("collapse",),
            },
        ),
        (
            "Heartbeat",
            {
                "fields": ("last_seen",),
            },
        ),
        (
            "Timestamps",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
        (
            "Audit",
            {
                "fields": ("created_by", "modified_by"),
                "classes": ("collapse",),
            },
        ),
    )

    def status_colored(self, obj: Worker) -> str:
        """Display status with color coding."""
        colors = {
            "online": "green",
            "busy": "orange",
            "draining": "purple",
            "offline": "gray",
        }
        color = colors.get(obj.status, "black")
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display(),
        )

    status_colored.short_description = "Status"

    def is_online_display(self, obj: Worker) -> bool:
        """Check if worker is online."""
        return obj.is_online()

    is_online_display.boolean = True
    is_online_display.short_description = "Online"

    def get_queryset(self, request: HttpRequest) -> QuerySet[Worker]:
        """Filter queryset based on user permissions."""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if request.user.has_perm("mirror_control_panel.view_all_workers"):
            return qs
        return qs.filter(current_job__project__owner=request.user)

    @admin.action(description="Force workers offline")
    def force_offline(self, request: HttpRequest, queryset: QuerySet[Worker]) -> None:
        """Force workers to offline status."""
        if not request.user.has_perm("mirror_control_panel.force_worker_offline"):
            self.message_user(
                request, "You don't have permission to force workers offline.", level="error"
            )
            return
        count = queryset.update(status=Worker.Status.OFFLINE)
        self.message_user(request, f"Force set {count} worker(s) to offline.")

    def save_model(self, request: HttpRequest, obj: Worker, form: Any, change: bool) -> None:
        """Save model with audit fields."""
        if not change:
            obj.created_by = request.user
        obj.modified_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Schedule)
class ScheduleAdmin(ModelAdmin):
    """Admin interface for Schedule."""

    list_display = [
        "name",
        "project",
        "url",
        "cron_expression",
        "enabled_indicator",
        "last_run",
        "next_run",
        "created_by",
    ]
    list_filter = ["enabled", "project", "created_at"]
    search_fields = ["name", "url", "cron_expression"]
    readonly_fields = [
        "created_at",
        "updated_at",
        "last_run",
        "next_run",
        "created_by",
        "modified_by",
    ]
    ordering = ["-created_at"]
    actions = ["enable_schedules", "disable_schedules"]
    fieldsets = (
        (None, {"fields": ("project", "name", "url", "cron_expression", "enabled")}),
        ("Crawl Configuration", {"fields": ("depth", "max_urls")}),
        ("Schedule Information", {"fields": ("last_run", "next_run")}),
        (
            "Metadata",
            {
                "fields": ("metadata",),
                "classes": ("collapse",),
            },
        ),
        (
            "Timestamps",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
        (
            "Audit",
            {
                "fields": ("created_by", "modified_by"),
                "classes": ("collapse",),
            },
        ),
    )

    def enabled_indicator(self, obj: Schedule) -> str:
        """Display enabled status with icon."""
        if obj.enabled:
            return "✅"
        return "❌"

    enabled_indicator.short_description = "Enabled"

    def get_queryset(self, request: HttpRequest) -> QuerySet[Schedule]:
        """Filter queryset based on user permissions."""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if request.user.has_perm("mirror_control_panel.view_all_schedules"):
            return qs
        return qs.filter(project__owner=request.user)

    def has_add_permission(self, request: HttpRequest) -> bool:
        """Check if user can add schedules."""
        return request.user.has_perm("mirror_control_panel.add_schedule")

    @admin.action(description="Enable selected schedules")
    def enable_schedules(self, request: HttpRequest, queryset: QuerySet[Schedule]) -> None:
        """Enable selected schedules."""
        if not request.user.has_perm("mirror_control_panel.change_schedule"):
            self.message_user(
                request, "You don't have permission to change schedules.", level="error"
            )
            return
        count = 0
        for schedule in queryset:
            schedule.enable()
            count += 1
        self.message_user(request, f"Enabled {count} schedule(s).")

    @admin.action(description="Disable selected schedules")
    def disable_schedules(self, request: HttpRequest, queryset: QuerySet[Schedule]) -> None:
        """Disable selected schedules."""
        if not request.user.has_perm("mirror_control_panel.change_schedule"):
            self.message_user(
                request, "You don't have permission to change schedules.", level="error"
            )
            return
        count = 0
        for schedule in queryset:
            schedule.disable()
            count += 1
        self.message_user(request, f"Disabled {count} schedule(s).")

    def save_model(self, request: HttpRequest, obj: Schedule, form: Any, change: bool) -> None:
        """Save model with audit fields."""
        if not change:
            obj.created_by = request.user
        obj.modified_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(AuditLog)
class AuditLogAdmin(ModelAdmin):
    """Admin interface for AuditLog - read-only."""

    list_display = [
        "timestamp",
        "user",
        "action",
        "resource_type",
        "resource_id",
        "ip_address",
    ]
    list_filter = ["action", "resource_type", "timestamp"]
    search_fields = ["user__username", "resource_type", "resource_id", "ip_address"]
    readonly_fields = [
        "user",
        "action",
        "resource_type",
        "resource_id",
        "changes",
        "ip_address",
        "user_agent",
        "timestamp",
        "metadata",
    ]
    ordering = ["-timestamp"]
    fieldsets = (
        (None, {"fields": ("user", "action", "timestamp")}),
        ("Resource", {"fields": ("resource_type", "resource_id")}),
        (
            "Changes",
            {
                "fields": ("changes",),
                "classes": ("collapse",),
            },
        ),
        ("Request Information", {"fields": ("ip_address", "user_agent")}),
        (
            "Additional",
            {
                "fields": ("metadata",),
                "classes": ("collapse",),
            },
        ),
    )

    def has_add_permission(self, request: HttpRequest) -> bool:
        """Audit logs cannot be created manually."""
        return False

    def has_change_permission(self, request: HttpRequest, obj: Optional[AuditLog] = None) -> bool:
        """Audit logs cannot be changed."""
        return False

    def has_delete_permission(self, request: HttpRequest, obj: Optional[AuditLog] = None) -> bool:
        """Audit logs cannot be deleted."""
        return False

    def get_queryset(self, request: HttpRequest) -> QuerySet[AuditLog]:
        """Filter queryset based on user permissions."""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if request.user.has_perm("mirror_control_panel.view_audit_logs"):
            return qs
        return qs.none()
