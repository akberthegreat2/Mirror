"""Tests for Mirror Control Panel services."""

import pytest
from django.contrib.auth import get_user_model

from mirror_control_panel.models import CrawlJob
from mirror_control_panel.services import CrawlService, ScheduleService

User = get_user_model()


@pytest.mark.django_db
class TestCrawlService:
    """Tests for CrawlService."""

    def test_start_crawl(self, user, project):
        """Test starting a crawl."""
        # Add user to Operator group
        from django.contrib.auth.models import Group

        operator_group, _ = Group.objects.get_or_create(name="Operator")
        user.groups.add(operator_group)

        service = CrawlService()
        job = service.start_crawl(
            project_id=project.id,
            url="https://example.com",
            user=user,
            depth=2,
            max_urls=100,
        )

        assert job.url == "https://example.com"
        assert job.depth == 2
        assert job.max_urls == 100
        assert job.status == CrawlJob.Status.PENDING
        assert job.created_by == user

    def test_start_crawl_without_permission(self, viewer_user, project):
        """Test starting a crawl without permission."""
        service = CrawlService()
        with pytest.raises(PermissionError, match="cannot start crawls"):
            service.start_crawl(
                project_id=project.id,
                url="https://example.com",
                user=viewer_user,
            )

    def test_start_crawl_other_project(self, user, operator_user):
        """Test starting a crawl in someone else's project."""
        from django.contrib.auth.models import Group

        operator_group, _ = Group.objects.get_or_create(name="Operator")
        user.groups.add(operator_group)

        # Create project owned by operator_user
        project = project = Project.objects.create(
            name="Other Project",
            owner=operator_user,
            created_by=operator_user,
        )

        service = CrawlService()
        with pytest.raises(PermissionError, match="does not own this project"):
            service.start_crawl(
                project_id=project.id,
                url="https://example.com",
                user=user,
            )

    def test_retry_crawl(self, user, project):
        """Test retrying a failed crawl."""
        from django.contrib.auth.models import Group

        operator_group, _ = Group.objects.get_or_create(name="Operator")
        user.groups.add(operator_group)

        # Create a failed crawl
        job = CrawlJob.objects.create(
            project=project,
            url="https://example.com",
            created_by=user,
        )
        job.mark_completed(success=False)

        service = CrawlService()
        retried = service.retry_crawl(job.id, user)

        assert retried.status == CrawlJob.Status.PENDING
        assert retried.completed_at is None
        assert retried.error_message == ""

    def test_retry_crawl_cannot_retry(self, user, project):
        """Test retrying a crawl that cannot be retried."""
        from django.contrib.auth.models import Group

        operator_group, _ = Group.objects.get_or_create(name="Operator")
        user.groups.add(operator_group)

        # Create a pending crawl
        job = CrawlJob.objects.create(
            project=project,
            url="https://example.com",
            created_by=user,
        )

        service = CrawlService()
        with pytest.raises(ValueError, match="cannot be retried"):
            service.retry_crawl(job.id, user)

    def test_cancel_crawl(self, user, project):
        """Test cancelling a running crawl."""
        from django.contrib.auth.models import Group

        operator_group, _ = Group.objects.get_or_create(name="Operator")
        user.groups.add(operator_group)

        # Create a running crawl
        job = CrawlJob.objects.create(
            project=project,
            url="https://example.com",
            created_by=user,
        )
        job.mark_started()

        service = CrawlService()
        cancelled = service.cancel_crawl(job.id, user)

        assert cancelled.status == CrawlJob.Status.CANCELLED
        assert cancelled.completed_at is not None

    def test_cancel_crawl_cannot_cancel(self, user, project):
        """Test cancelling a crawl that cannot be cancelled."""
        from django.contrib.auth.models import Group

        operator_group, _ = Group.objects.get_or_create(name="Operator")
        user.groups.add(operator_group)

        # Create a pending crawl
        job = CrawlJob.objects.create(
            project=project,
            url="https://example.com",
            created_by=user,
        )

        service = CrawlService()
        with pytest.raises(ValueError, match="cannot be cancelled"):
            service.cancel_crawl(job.id, user)


@pytest.mark.django_db
class TestScheduleService:
    """Tests for ScheduleService."""

    def test_create_schedule(self, user, project):
        """Test creating a schedule."""
        from django.contrib.auth.models import Group

        operator_group, _ = Group.objects.get_or_create(name="Operator")
        user.groups.add(operator_group)

        service = ScheduleService()
        schedule = service.create_schedule(
            project_id=project.id,
            name="Daily Crawl",
            url="https://example.com",
            cron_expression="0 2 * * *",
            user=user,
            depth=2,
        )

        assert schedule.name == "Daily Crawl"
        assert schedule.url == "https://example.com"
        assert schedule.cron_expression == "0 2 * * *"
        assert schedule.depth == 2
        assert schedule.enabled is True

    def test_create_schedule_without_permission(self, viewer_user, project):
        """Test creating a schedule without permission."""
        service = ScheduleService()
        with pytest.raises(PermissionError, match="cannot add schedules"):
            service.create_schedule(
                project_id=project.id,
                name="Daily Crawl",
                url="https://example.com",
                cron_expression="0 2 * * *",
                user=viewer_user,
            )
