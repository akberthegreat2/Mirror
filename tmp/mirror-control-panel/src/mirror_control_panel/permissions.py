"""Permissions and groups for Mirror Control Panel."""

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

from mirror_control_panel.models import (
    ArchiveRecord,
    AuditLog,
    CrawlJob,
    CrawledURL,
    Project,
    Schedule,
    Worker,
)


def setup_groups() -> None:
    """Create default groups with appropriate permissions.

    Groups:
        Viewer: Read-only access to all models
        Operator: Can start/retry crawls, manage schedules
        Admin: Full access including user management
    """
    # Get content types for all models
    content_types = {
        "project": ContentType.objects.get_for_model(Project),
        "crawljob": ContentType.objects.get_for_model(CrawlJob),
        "crawledurl": ContentType.objects.get_for_model(CrawledURL),
        "archiverecord": ContentType.objects.get_for_model(ArchiveRecord),
        "worker": ContentType.objects.get_for_model(Worker),
        "schedule": ContentType.objects.get_for_model(Schedule),
        "auditlog": ContentType.objects.get_for_model(AuditLog),
    }

    # Create groups
    viewer_group, _ = Group.objects.get_or_create(name="Viewer")
    operator_group, _ = Group.objects.get_or_create(name="Operator")
    admin_group, _ = Group.objects.get_or_create(name="Admin")

    # Clear existing permissions
    viewer_group.permissions.clear()
    operator_group.permissions.clear()
    admin_group.permissions.clear()

    # Viewer permissions - read-only
    viewer_permissions = [
        ("view_project", content_types["project"]),
        ("view_crawljob", content_types["crawljob"]),
        ("view_crawledurl", content_types["crawledurl"]),
        ("view_archiverecord", content_types["archiverecord"]),
        ("view_worker", content_types["worker"]),
        ("view_schedule", content_types["schedule"]),
        ("view_audit_logs", content_types["auditlog"]),
    ]

    for codename, ct in viewer_permissions:
        permission, _ = Permission.objects.get_or_create(
            codename=codename,
            content_type=ct,
        )
        viewer_group.permissions.add(permission)

    # Operator permissions - everything Viewer can do + actions
    operator_permissions = viewer_permissions + [
        ("add_crawljob", content_types["crawljob"]),
        ("change_crawljob", content_types["crawljob"]),
        ("retry_crawl", content_types["crawljob"]),
        ("cancel_crawl", content_types["crawljob"]),
        ("add_schedule", content_types["schedule"]),
        ("change_schedule", content_types["schedule"]),
        ("add_project", content_types["project"]),
        ("change_project", content_types["project"]),
        ("add_crawledurl", content_types["crawledurl"]),
        ("add_archiverecord", content_types["archiverecord"]),
    ]

    for codename, ct in operator_permissions:
        permission, _ = Permission.objects.get_or_create(
            codename=codename,
            content_type=ct,
        )
        operator_group.permissions.add(permission)

    # Admin permissions - everything
    admin_permissions = operator_permissions + [
        ("delete_project", content_types["project"]),
        ("delete_crawljob", content_types["crawljob"]),
        ("delete_crawledurl", content_types["crawledurl"]),
        ("delete_archiverecord", content_types["archiverecord"]),
        ("delete_worker", content_types["worker"]),
        ("delete_schedule", content_types["schedule"]),
        ("force_worker_offline", content_types["worker"]),
        ("view_all_projects", content_types["project"]),
        ("view_all_crawls", content_types["crawljob"]),
        ("view_all_workers", content_types["worker"]),
        ("view_all_schedules", content_types["schedule"]),
        ("delete_any_project", content_types["project"]),
    ]

    for codename, ct in admin_permissions:
        permission, _ = Permission.objects.get_or_create(
            codename=codename,
            content_type=ct,
        )
        admin_group.permissions.add(permission)


def get_user_permissions(user) -> set[str]:
    """Get all permission codenames for a user.

    Args:
        user: Django User instance

    Returns:
        Set of permission codenames (e.g., {'add_crawljob', 'retry_crawl'})
    """
    if user.is_superuser:
        return {
            f"{perm.content_type.app_label}.{perm.codename}" for perm in Permission.objects.all()
        }
    return set(user.get_all_permissions())


def user_can_retry_crawl(user, crawl: CrawlJob) -> bool:
    """Check if user can retry a specific crawl.

    Args:
        user: Django User instance
        crawl: CrawlJob instance

    Returns:
        True if user can retry the crawl
    """
    if user.is_superuser:
        return True

    if not user.has_perm("mirror_control_panel.retry_crawl"):
        return False

    # Operator can retry their own project's crawls
    if user.has_perm("mirror_control_panel.view_all_crawls"):
        return True

    return crawl.project.owner == user


def user_can_cancel_crawl(user, crawl: CrawlJob) -> bool:
    """Check if user can cancel a specific crawl.

    Args:
        user: Django User instance
        crawl: CrawlJob instance

    Returns:
        True if user can cancel the crawl
    """
    if user.is_superuser:
        return True

    if not user.has_perm("mirror_control_panel.cancel_crawl"):
        return False

    if user.has_perm("mirror_control_panel.view_all_crawls"):
        return True

    return crawl.project.owner == user


def user_can_view_project(user, project: Project) -> bool:
    """Check if user can view a specific project.

    Args:
        user: Django User instance
        project: Project instance

    Returns:
        True if user can view the project
    """
    if user.is_superuser:
        return True

    if user.has_perm("mirror_control_panel.view_all_projects"):
        return True

    return project.owner == user


def user_can_manage_project(user, project: Project) -> bool:
    """Check if user can manage (edit/delete) a specific project.

    Args:
        user: Django User instance
        project: Project instance

    Returns:
        True if user can manage the project
    """
    if user.is_superuser:
        return True

    if user.has_perm("mirror_control_panel.delete_any_project"):
        return True

    return project.owner == user
