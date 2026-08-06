"""Integration tests for Mirror Control Panel."""

import pytest
from django.contrib.auth import get_user_model

from mirror_control_panel.models import CrawlJob, Project
from mirror_control_panel.services import CrawlService

User = get_user_model()


@pytest.mark.django_db
class TestIntegration:
    """Integration tests for the full flow."""

    def test_full_crawl_flow_with_mirror_core(self, user, project):
        """Test the complete crawl flow with Mirror Core integration."""
        from django.contrib.auth.models import Group

        operator_group, _ = Group.objects.get_or_create(name="Operator")
        user.groups.add(operator_group)

        # 1. Create a project
        project = Project.objects.create(
            name="Integration Test",
            owner=user,
            created_by=user,
        )

        # 2. Start a crawl
        service = CrawlService()
        job = service.start_crawl(
            project_id=project.id,
            url="https://example.com",
            user=user,
            depth=1,
        )

        # 3. Verify job was created
        assert job.project == project
        assert job.url == "https://example.com"
        assert job.status == CrawlJob.Status.PENDING
        assert job.created_by == user

        # 4. Verify can retry if failed
        job.mark_completed(success=False)
        retried = service.retry_crawl(job.id, user)
        assert retried.status == CrawlJob.Status.PENDING

        # 5. Verify can cancel if running
        retried.mark_started()
        cancelled = service.cancel_crawl(retried.id, user)
        assert cancelled.status == CrawlJob.Status.CANCELLED

    def test_audit_log_created_on_crawl_start(self, user, project):
        """Test audit log is created when starting a crawl."""
        from django.contrib.auth.models import Group

        operator_group, _ = Group.objects.get_or_create(name="Operator")
        user.groups.add(operator_group)

        from mirror_control_panel.models import AuditLog

        service = CrawlService()
        job = service.start_crawl(
            project_id=project.id,
            url="https://example.com",
            user=user,
        )

        # Check audit log was created
        logs = AuditLog.objects.filter(
            user=user,
            resource_type="CrawlJob",
            resource_id=str(job.id),
        )
        assert logs.exists()

    def test_permission_flow(self, user, operator_user, project):
        """Test permission checks throughout the flow."""
        from django.contrib.auth.models import Group

        operator_group, _ = Group.objects.get_or_create(name="Operator")
        user.groups.add(operator_group)

        # Create project owned by user
        project = Project.objects.create(
            name="User Project",
            owner=user,
            created_by=user,
        )

        # User can start crawl
        service = CrawlService()
        job = service.start_crawl(
            project_id=project.id,
            url="https://example.com",
            user=user,
        )

        # Operator user cannot retry (doesn't own project)
        with pytest.raises(PermissionError, match="does not own this crawl"):
            service.retry_crawl(job.id, operator_user)

        # But can if given view_all permission
        from django.contrib.auth.models import Permission
        from django.contrib.contenttypes.models import ContentType
        from mirror_control_panel.models import CrawlJob

        content_type = ContentType.objects.get_for_model(CrawlJob)
        permission, _ = Permission.objects.get_or_create(
            codename="view_all_crawls",
            content_type=content_type,
        )
        operator_user.user_permissions.add(permission)

        # Still can't retry without retry permission
        # Add retry permission too
        retry_perm, _ = Permission.objects.get_or_create(
            codename="retry_crawl",
            content_type=content_type,
        )
        operator_user.user_permissions.add(retry_perm)

        # Now should work
        job.mark_completed(success=False)
        service.retry_crawl(job.id, operator_user)
