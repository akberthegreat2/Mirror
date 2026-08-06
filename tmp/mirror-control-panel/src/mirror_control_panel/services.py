"""Service layer for Mirror Control Panel - business logic and Mirror integration."""

from __future__ import annotations

import asyncio
import logging
from typing import Optional

from django.contrib.auth import get_user_model
from django.db import transaction

from mirror_core.application import Application
from mirror_core.pipeline import Pipeline
from mirror_core.settings import MirrorSettings

from mirror_control_panel.models import CrawlJob, Project, Schedule
from mirror_control_panel.permissions import user_can_cancel_crawl, user_can_retry_crawl

logger = logging.getLogger(__name__)
User = get_user_model()


class CrawlService:
    """Service for managing crawl lifecycle and Mirror integration."""

    def __init__(self, app: Optional[Application] = None) -> None:
        """Initialize CrawlService.

        Args:
            app: Mirror Application instance. If None, a new one will be created.
        """
        self._app = app
        self._app_owned = app is None

    @property
    def app(self) -> Application:
        """Get or create Mirror Application instance."""
        if self._app is None:
            settings = MirrorSettings()
            self._app = Application(settings=settings)
        return self._app

    async def _ensure_started(self) -> None:
        """Ensure the application is started."""
        if not self.app.started:
            await self.app.start()

    async def start_crawl(
        self,
        project_id: int,
        url: str,
        user: User,
        depth: int = 1,
        max_urls: Optional[int] = None,
        pipeline: Optional[Pipeline] = None,
    ) -> CrawlJob:
        """Start a new crawl.

        Args:
            project_id: ID of the project to crawl for
            url: URL to crawl
            user: User starting the crawl
            depth: Maximum crawl depth
            max_urls: Maximum URLs to crawl
            pipeline: Optional custom pipeline

        Returns:
            CrawlJob instance

        Raises:
            PermissionError: If user cannot start crawls
            Project.DoesNotExist: If project not found
        """
        # Check permissions
        if not user.has_perm("mirror_control_panel.add_crawljob"):
            raise PermissionError("User cannot start crawls")

        # Get project
        project = Project.objects.get(id=project_id)

        # Check project ownership
        if project.owner != user and not user.has_perm("mirror_control_panel.view_all_crawls"):
            raise PermissionError("User does not own this project")

        # Create job with user context
        with transaction.atomic():
            job = CrawlJob.objects.create(
                project=project,
                url=url,
                depth=depth,
                max_urls=max_urls,
                status=CrawlJob.Status.PENDING,
                created_by=user,
                modified_by=user,
            )

        # Start execution in background
        await self._execute_crawl(job.id, user, pipeline)

        return job

    async def _execute_crawl(
        self,
        job_id: int,
        user: User,
        pipeline: Optional[Pipeline] = None,
    ) -> None:
        """Execute a crawl job.

        Args:
            job_id: CrawlJob ID
            user: User who started the crawl
            pipeline: Optional custom pipeline
        """
        job = CrawlJob.objects.get(id=job_id)

        try:
            # Update status to running
            job.mark_started()

            # Ensure app is started
            await self._ensure_started()

            # Build pipeline if not provided
            if pipeline is None:
                # Build a default crawl pipeline
                # This would normally be configured via settings
                pipeline = Pipeline(
                    id=f"crawl-{job.id}",
                    steps=[],
                )

            # Execute with user context
            result = await self.app.run_pipeline_detailed(
                pipeline,
                inputs={
                    "url": job.url,
                    "job_id": str(job.id),
                    "user_id": user.id,
                    "depth": job.depth,
                    "max_urls": job.max_urls,
                },
            )

            # Update job status
            if result.outcome.value == "succeeded":
                job.mark_completed(success=True)
            else:
                job.mark_completed(success=False, error=result.error_message)

            logger.info(f"Crawl {job.id} completed with status {job.status}")

        except Exception as e:
            job.mark_completed(success=False, error=str(e))
            logger.error(f"Crawl {job.id} failed: {e}", exc_info=True)

    def retry_crawl(self, job_id: int, user: User) -> CrawlJob:
        """Retry a failed or cancelled crawl.

        Args:
            job_id: CrawlJob ID
            user: User retrying the crawl

        Returns:
            CrawlJob instance

        Raises:
            PermissionError: If user cannot retry crawls
            ValueError: If crawl cannot be retried
        """
        job = CrawlJob.objects.get(id=job_id)

        # Check permissions
        if not user.has_perm("mirror_control_panel.retry_crawl"):
            raise PermissionError("User cannot retry crawls")

        if not user_can_retry_crawl(user, job):
            raise PermissionError("User does not own this crawl")

        if not job.can_retry():
            raise ValueError(f"Crawl {job_id} cannot be retried (status: {job.status})")

        # Reset and run again
        with transaction.atomic():
            job.retry()

        # Execute in background
        asyncio.create_task(self._execute_crawl(job.id, user))

        return job

    def cancel_crawl(self, job_id: int, user: User) -> CrawlJob:
        """Cancel a running crawl.

        Args:
            job_id: CrawlJob ID
            user: User cancelling the crawl

        Returns:
            CrawlJob instance

        Raises:
            PermissionError: If user cannot cancel crawls
            ValueError: If crawl cannot be cancelled
        """
        job = CrawlJob.objects.get(id=job_id)

        # Check permissions
        if not user.has_perm("mirror_control_panel.cancel_crawl"):
            raise PermissionError("User cannot cancel crawls")

        if not user_can_cancel_crawl(user, job):
            raise PermissionError("User does not own this crawl")

        if not job.can_cancel():
            raise ValueError(f"Crawl {job_id} cannot be cancelled (status: {job.status})")

        # Cancel the crawl
        with transaction.atomic():
            job.mark_cancelled()

        # If there's an execution, cancel it
        if job.execution_id and self.app.executor:
            try:
                self.app.executor.cancel()
            except Exception as e:
                logger.warning(f"Failed to cancel execution {job.execution_id}: {e}")

        return job

    async def shutdown(self) -> None:
        """Shutdown the Mirror application."""
        if self._app_owned and self._app and self._app.started:
            await self._app.shutdown()


class ScheduleService:
    """Service for managing scheduled crawls."""

    def __init__(self, crawl_service: Optional[CrawlService] = None) -> None:
        """Initialize ScheduleService.

        Args:
            crawl_service: Optional CrawlService instance
        """
        self.crawl_service = crawl_service or CrawlService()

    def create_schedule(
        self,
        project_id: int,
        name: str,
        url: str,
        cron_expression: str,
        user: User,
        depth: int = 1,
        max_urls: Optional[int] = None,
    ) -> Schedule:
        """Create a new schedule.

        Args:
            project_id: ID of the project
            name: Schedule name
            url: URL to crawl
            cron_expression: Cron expression
            user: User creating the schedule
            depth: Maximum crawl depth
            max_urls: Maximum URLs to crawl

        Returns:
            Schedule instance

        Raises:
            PermissionError: If user cannot add schedules
        """
        if not user.has_perm("mirror_control_panel.add_schedule"):
            raise PermissionError("User cannot add schedules")

        project = Project.objects.get(id=project_id)
        if project.owner != user and not user.has_perm("mirror_control_panel.view_all_schedules"):
            raise PermissionError("User does not own this project")

        with transaction.atomic():
            schedule = Schedule.objects.create(
                project=project,
                name=name,
                url=url,
                cron_expression=cron_expression,
                depth=depth,
                max_urls=max_urls,
                enabled=True,
                created_by=user,
                modified_by=user,
            )

        return schedule

    def run_schedule(self, schedule_id: int, user: User) -> CrawlJob:
        """Execute a schedule now.

        Args:
            schedule_id: Schedule ID
            user: User executing the schedule

        Returns:
            CrawlJob instance

        Raises:
            PermissionError: If user cannot run the schedule
        """
        schedule = Schedule.objects.get(id=schedule_id)

        if not user.has_perm("mirror_control_panel.add_crawljob"):
            raise PermissionError("User cannot start crawls")

        if schedule.project.owner != user and not user.has_perm(
            "mirror_control_panel.view_all_schedules"
        ):
            raise PermissionError("User does not own this project")

        # Create crawl job from schedule
        job = asyncio.run(
            self.crawl_service.start_crawl(
                project_id=schedule.project.id,
                url=schedule.url,
                user=user,
                depth=schedule.depth,
                max_urls=schedule.max_urls,
            )
        )

        # Mark schedule as run
        schedule.mark_run()

        return job


class WorkerService:
    """Service for managing workers."""

    @staticmethod
    def update_heartbeat(worker_name: str) -> None:
        """Update a worker's heartbeat.

        Args:
            worker_name: Name of the worker

        Returns:
            None
        """
        from mirror_control_panel.models import Worker

        try:
            worker = Worker.objects.get(name=worker_name)
            worker.heartbeat()
        except Worker.DoesNotExist:
            # Create worker if it doesn't exist
            Worker.objects.create(
                name=worker_name,
                status=Worker.Status.ONLINE,
            )

    @staticmethod
    def set_worker_status(worker_name: str, status: str) -> None:
        """Set a worker's status.

        Args:
            worker_name: Name of the worker
            status: New status

        Returns:
            None
        """
        from mirror_control_panel.models import Worker

        try:
            worker = Worker.objects.get(name=worker_name)
            worker.set_status(status)
        except Worker.DoesNotExist:
            Worker.objects.create(
                name=worker_name,
                status=status,
            )
