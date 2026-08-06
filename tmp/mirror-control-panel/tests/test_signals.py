"""Tests for Mirror Control Panel signal handlers."""

import pytest
from django.contrib.auth import get_user_model

from mirror_control_panel.models import ArchiveRecord, CrawlJob, CrawledURL, Worker
from mirror_control_panel.signals import (
    on_archive_created,
    on_crawl_completed,
    on_url_discovered,
    on_worker_heartbeat,
)

User = get_user_model()


@pytest.mark.django_db
class TestSignalHandlers:
    """Tests for signal handlers."""

    @pytest.mark.asyncio
    async def test_on_url_discovered(self, project, user):
        """Test url_discovered signal handler."""
        # Create crawl job
        job = CrawlJob.objects.create(
            project=project,
            url="https://example.com",
            created_by=user,
        )

        # Call handler
        await on_url_discovered(
            job_id=str(job.id),
            url="https://example.com/page",
            depth=1,
            user_id=user.id,
        )

        # Check record was created
        assert CrawledURL.objects.filter(crawl=job, url="https://example.com/page").exists()
        url_record = CrawledURL.objects.get(crawl=job, url="https://example.com/page")
        assert url_record.depth == 1
        assert url_record.created_by == user

    @pytest.mark.asyncio
    async def test_on_url_discovered_updates_depth(self, project, user):
        """Test url_discovered updates depth if URL exists."""
        job = CrawlJob.objects.create(
            project=project,
            url="https://example.com",
            created_by=user,
        )

        # Create existing record
        CrawledURL.objects.create(
            crawl=job,
            url="https://example.com/page",
            depth=1,
            created_by=user,
        )

        # Call handler with deeper depth
        await on_url_discovered(
            job_id=str(job.id),
            url="https://example.com/page",
            depth=3,
            user_id=user.id,
        )

        url_record = CrawledURL.objects.get(crawl=job, url="https://example.com/page")
        assert url_record.depth == 3

    @pytest.mark.asyncio
    async def test_on_archive_created(self, project, user):
        """Test archive_created signal handler."""
        job = CrawlJob.objects.create(
            project=project,
            url="https://example.com",
            created_by=user,
        )

        await on_archive_created(
            job_id=str(job.id),
            url="https://example.com",
            blob_key="archives/example.warc.gz",
            format="warc",
            size=1024000,
            checksum="sha256:abc123",
            user_id=user.id,
        )

        assert ArchiveRecord.objects.filter(crawl=job, blob_key="archives/example.warc.gz").exists()
        record = ArchiveRecord.objects.get(crawl=job, blob_key="archives/example.warc.gz")
        assert record.format == "warc"
        assert record.size == 1024000

    @pytest.mark.asyncio
    async def test_on_crawl_completed_success(self, project, user):
        """Test crawl_completed signal handler for success."""
        job = CrawlJob.objects.create(
            project=project,
            url="https://example.com",
            created_by=user,
        )
        job.mark_started()

        await on_crawl_completed(
            job_id=str(job.id),
            success=True,
        )

        job.refresh_from_db()
        assert job.status == CrawlJob.Status.SUCCEEDED

    @pytest.mark.asyncio
    async def test_on_crawl_completed_failure(self, project, user):
        """Test crawl_completed signal handler for failure."""
        job = CrawlJob.objects.create(
            project=project,
            url="https://example.com",
            created_by=user,
        )
        job.mark_started()

        await on_crawl_completed(
            job_id=str(job.id),
            success=False,
            error="Test error",
        )

        job.refresh_from_db()
        assert job.status == CrawlJob.Status.FAILED
        assert job.error_message == "Test error"

    @pytest.mark.asyncio
    async def test_on_worker_heartbeat_new_worker(self):
        """Test worker_heartbeat signal handler creates new worker."""
        await on_worker_heartbeat(
            worker_name="worker-1",
            status="online",
        )

        assert Worker.objects.filter(name="worker-1").exists()
        worker = Worker.objects.get(name="worker-1")
        assert worker.status == Worker.Status.ONLINE

    @pytest.mark.asyncio
    async def test_on_worker_heartbeat_existing_worker(self):
        """Test worker_heartbeat signal handler updates existing worker."""
        worker = Worker.objects.create(
            name="worker-1",
            status=Worker.Status.OFFLINE,
        )

        await on_worker_heartbeat(
            worker_name="worker-1",
            status="online",
        )

        worker.refresh_from_db()
        assert worker.status == Worker.Status.ONLINE
        assert worker.last_seen is not None
