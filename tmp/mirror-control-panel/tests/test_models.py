"""Tests for Mirror Control Panel models."""

import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.utils import timezone

from mirror_control_panel.models import (
    ArchiveRecord,
    AuditLog,
    CrawlJob,
    CrawledURL,
    Project,
    Schedule,
    Worker,
)

User = get_user_model()


@pytest.mark.django_db
class TestProject:
    """Tests for Project model."""

    def test_create_project(self, user):
        """Test creating a project."""
        project = Project.objects.create(
            name="Test Project",
            owner=user,
            created_by=user,
        )
        assert project.name == "Test Project"
        assert project.owner == user
        assert project.is_active is True
        assert project.slug == "test-project"

    def test_project_str(self, user):
        """Test string representation."""
        project = Project.objects.create(
            name="Test Project",
            owner=user,
            created_by=user,
        )
        assert str(project) == f"Test Project (owner: {user.username})"

    def test_project_unique_name(self, user):
        """Test project name must be unique."""
        Project.objects.create(name="Unique", owner=user, created_by=user)
        with pytest.raises(IntegrityError):
            Project.objects.create(name="Unique", owner=user, created_by=user)


@pytest.mark.django_db
class TestCrawlJob:
    """Tests for CrawlJob model."""

    def test_create_crawl_job(self, project, user):
        """Test creating a crawl job."""
        job = CrawlJob.objects.create(
            project=project,
            url="https://example.com",
            depth=2,
            max_urls=100,
            created_by=user,
        )
        assert job.url == "https://example.com"
        assert job.depth == 2
        assert job.status == CrawlJob.Status.PENDING

    def test_crawl_job_str(self, project, user):
        """Test string representation."""
        job = CrawlJob.objects.create(
            project=project,
            url="https://example.com",
            created_by=user,
        )
        assert str(job) == "Crawl https://example.com (pending)"

    def test_mark_started(self, project, user):
        """Test marking a job as started."""
        job = CrawlJob.objects.create(
            project=project,
            url="https://example.com",
            created_by=user,
        )
        assert job.started_at is None
        job.mark_started()
        assert job.status == CrawlJob.Status.RUNNING
        assert job.started_at is not None

    def test_mark_completed_success(self, project, user):
        """Test marking a job as completed successfully."""
        job = CrawlJob.objects.create(
            project=project,
            url="https://example.com",
            created_by=user,
        )
        job.mark_completed(success=True)
        assert job.status == CrawlJob.Status.SUCCEEDED
        assert job.completed_at is not None

    def test_mark_completed_failure(self, project, user):
        """Test marking a job as failed."""
        job = CrawlJob.objects.create(
            project=project,
            url="https://example.com",
            created_by=user,
        )
        job.mark_completed(success=False, error="Test error")
        assert job.status == CrawlJob.Status.FAILED
        assert job.error_message == "Test error"

    def test_retry(self, project, user):
        """Test retrying a failed job."""
        job = CrawlJob.objects.create(
            project=project,
            url="https://example.com",
            created_by=user,
        )
        job.mark_completed(success=False)
        assert job.status == CrawlJob.Status.FAILED

        job.retry()
        assert job.status == CrawlJob.Status.PENDING
        assert job.completed_at is None
        assert job.error_message == ""

    def test_can_retry(self, project, user):
        """Test can_retry method."""
        job = CrawlJob.objects.create(
            project=project,
            url="https://example.com",
            created_by=user,
        )
        assert job.can_retry() is False

        job.mark_completed(success=False)
        assert job.can_retry() is True

    def test_can_cancel(self, project, user):
        """Test can_cancel method."""
        job = CrawlJob.objects.create(
            project=project,
            url="https://example.com",
            created_by=user,
        )
        assert job.can_cancel() is False

        job.mark_started()
        assert job.can_cancel() is True


@pytest.mark.django_db
class TestCrawledURL:
    """Tests for CrawledURL model."""

    def test_create_crawled_url(self, crawl_job, user):
        """Test creating a crawled URL."""
        url = CrawledURL.objects.create(
            crawl=crawl_job,
            url="https://example.com/page",
            depth=1,
            status_code=200,
            created_by=user,
        )
        assert url.url == "https://example.com/page"
        assert url.depth == 1
        assert url.status_code == 200

    def test_crawled_url_str(self, crawl_job, user):
        """Test string representation."""
        url = CrawledURL.objects.create(
            crawl=crawl_job,
            url="https://example.com/page",
            depth=2,
            created_by=user,
        )
        assert str(url) == "https://example.com/page (depth 2)"

    def test_crawled_url_unique_crawl_url(self, crawl_job, user):
        """Test that (crawl, url) must be unique."""
        url = "https://example.com/page"
        CrawledURL.objects.create(
            crawl=crawl_job,
            url=url,
            created_by=user,
        )
        with pytest.raises(IntegrityError):
            CrawledURL.objects.create(
                crawl=crawl_job,
                url=url,
                created_by=user,
            )


@pytest.mark.django_db
class TestArchiveRecord:
    """Tests for ArchiveRecord model."""

    def test_create_archive_record(self, crawl_job, user):
        """Test creating an archive record."""
        record = ArchiveRecord.objects.create(
            crawl=crawl_job,
            url="https://example.com",
            blob_key="archives/example.warc.gz",
            format=ArchiveRecord.Format.WARC,
            size=1024000,
            checksum="sha256:abc123",
            created_by=user,
        )
        assert record.blob_key == "archives/example.warc.gz"
        assert record.format == ArchiveRecord.Format.WARC
        assert record.size == 1024000

    def test_archive_record_str(self, crawl_job, user):
        """Test string representation."""
        record = ArchiveRecord.objects.create(
            crawl=crawl_job,
            url="https://example.com",
            blob_key="archives/example.warc.gz",
            created_by=user,
        )
        assert str(record) == "Archive archives/example.warc.gz (warc)"


@pytest.mark.django_db
class TestWorker:
    """Tests for Worker model."""

    def test_create_worker(self, user):
        """Test creating a worker."""
        worker = Worker.objects.create(
            name="worker-1",
            status=Worker.Status.ONLINE,
            created_by=user,
        )
        assert worker.name == "worker-1"
        assert worker.status == Worker.Status.ONLINE

    def test_worker_str(self, user):
        """Test string representation."""
        worker = Worker.objects.create(
            name="worker-1",
            status=Worker.Status.ONLINE,
            created_by=user,
        )
        assert str(worker) == "worker-1 (Online)"

    def test_heartbeat(self, user):
        """Test worker heartbeat update."""
        worker = Worker.objects.create(
            name="worker-1",
            created_by=user,
        )
        assert worker.last_seen is None
        worker.heartbeat()
        assert worker.last_seen is not None

    def test_is_online(self, user):
        """Test is_online method."""
        worker = Worker.objects.create(
            name="worker-1",
            status=Worker.Status.ONLINE,
            created_by=user,
        )
        # Without heartbeat, should be False
        assert worker.is_online() is False

        # With recent heartbeat
        worker.last_seen = timezone.now()
        worker.save()
        assert worker.is_online() is True

        # With old heartbeat
        worker.last_seen = timezone.now() - timezone.timedelta(seconds=120)
        worker.save()
        assert worker.is_online() is False


@pytest.mark.django_db
class TestSchedule:
    """Tests for Schedule model."""

    def test_create_schedule(self, project, user):
        """Test creating a schedule."""
        schedule = Schedule.objects.create(
            project=project,
            name="Daily Crawl",
            url="https://example.com",
            cron_expression="0 2 * * *",
            created_by=user,
        )
        assert schedule.name == "Daily Crawl"
        assert schedule.url == "https://example.com"
        assert schedule.cron_expression == "0 2 * * *"
        assert schedule.enabled is True

    def test_schedule_str(self, project, user):
        """Test string representation."""
        schedule = Schedule.objects.create(
            project=project,
            name="Daily Crawl",
            url="https://example.com",
            cron_expression="0 2 * * *",
            created_by=user,
        )
        assert str(schedule) == "Daily Crawl (0 2 * * *) - enabled"

    def test_enable_disable(self, project, user):
        """Test enabling and disabling schedules."""
        schedule = Schedule.objects.create(
            project=project,
            name="Daily Crawl",
            url="https://example.com",
            cron_expression="0 2 * * *",
            enabled=False,
            created_by=user,
        )
        assert schedule.enabled is False

        schedule.enable()
        assert schedule.enabled is True

        schedule.disable()
        assert schedule.enabled is False


@pytest.mark.django_db
class TestAuditLog:
    """Tests for AuditLog model."""

    def test_create_audit_log(self, user):
        """Test creating an audit log entry."""
        log = AuditLog.objects.create(
            user=user,
            action=AuditLog.Action.CREATE,
            resource_type="Project",
            resource_id="1",
            changes={"name": "Test"},
            ip_address="127.0.0.1",
            user_agent="test-agent",
        )
        assert log.user == user
        assert log.action == AuditLog.Action.CREATE
        assert log.resource_type == "Project"

    def test_audit_log_immutable(self, user):
        """Test that audit logs cannot be updated or deleted."""
        log = AuditLog.objects.create(
            user=user,
            action=AuditLog.Action.CREATE,
            resource_type="Project",
            resource_id="1",
        )

        with pytest.raises(RuntimeError, match="immutable"):
            log.delete()

        with pytest.raises(RuntimeError, match="immutable"):
            log.save()

    def test_audit_log_str(self, user):
        """Test string representation."""
        log = AuditLog.objects.create(
            user=user,
            action=AuditLog.Action.CREATE,
            resource_type="Project",
            resource_id="1",
        )
        assert str(log).startswith(f"{user.username} create Project 1 at")
