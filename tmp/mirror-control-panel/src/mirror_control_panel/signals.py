"""Signal bridge between Mirror Core's SignalBus and Django ORM.

This module connects Mirror's async signal bus to Django's synchronous ORM
using sync_to_async bridges.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from asgiref.sync import sync_to_async
from django.db import transaction

from mirror_core.signals import SignalBus
from mirror_core.application import Application


logger = logging.getLogger(__name__)

# Global signal bus reference
_signal_bus: Optional[SignalBus] = None


def get_signal_bus() -> SignalBus:
    """Get or create the global signal bus.

    Returns:
        SignalBus instance
    """
    global _signal_bus
    if _signal_bus is None:
        _signal_bus = SignalBus()
    return _signal_bus


def register_handlers() -> None:
    """Register all Django signal handlers with Mirror's signal bus.

    This should be called when the Django app starts.
    """
    bus = get_signal_bus()

    # Subscribe to Mirror signals
    bus.subscribe("url_discovered", on_url_discovered)
    bus.subscribe("archive_created", on_archive_created)
    bus.subscribe("crawl_completed", on_crawl_completed)
    bus.subscribe("worker_heartbeat", on_worker_heartbeat)
    bus.subscribe("crawl_started", on_crawl_started)

    logger.info("Registered Django signal handlers with Mirror SignalBus")


# ============================================================================
# Signal Handlers
# ============================================================================


async def on_url_discovered(
    job_id: str,
    url: str,
    depth: int,
    user_id: Optional[int] = None,
    **kwargs: Any,
) -> None:
    """Handle url_discovered signal from Mirror Core.

    Creates a CrawledURL record in the database.

    Args:
        job_id: ID of the crawl job
        url: Discovered URL
        depth: Depth at which URL was discovered
        user_id: ID of the user who initiated the crawl
        **kwargs: Additional signal data
    """
    try:
        await sync_to_async(_save_crawled_url)(job_id, url, depth, user_id)
        logger.debug(f"Saved discovered URL: {url} for job {job_id}")
    except Exception as e:
        logger.error(f"Failed to save discovered URL {url}: {e}", exc_info=True)


@sync_to_async
def _save_crawled_url(
    job_id: str,
    url: str,
    depth: int,
    user_id: Optional[int] = None,
) -> None:
    """Synchronous helper to save a CrawledURL.

    Args:
        job_id: ID of the crawl job
        url: Discovered URL
        depth: Depth at which URL was discovered
        user_id: ID of the user who initiated the crawl
    """
    from mirror_control_panel.models import CrawlJob

    with transaction.atomic():
        # Get the crawl job
        try:
            job = CrawlJob.objects.get(id=job_id)
        except CrawlJob.DoesNotExist:
            logger.warning(f"CrawlJob {job_id} not found, skipping URL save")
            return

        # Check if URL already exists for this crawl
        existing, created = CrawledURL.objects.get_or_create(
            crawl=job,
            url=url,
            defaults={
                "depth": depth,
                "created_by_id": user_id,
            },
        )
        if not created:
            # Update depth if it's deeper
            if depth > existing.depth:
                existing.depth = depth
                existing.save(update_fields=["depth"])


async def on_archive_created(
    job_id: str,
    url: str,
    blob_key: str,
    format: str = "warc",
    size: Optional[int] = None,
    checksum: Optional[str] = None,
    user_id: Optional[int] = None,
    **kwargs: Any,
) -> None:
    """Handle archive_created signal from Mirror Core.

    Creates an ArchiveRecord in the database.

    Args:
        job_id: ID of the crawl job
        url: URL that was archived
        blob_key: Key/path in blob storage
        format: Archive format (warc, json, html, etc.)
        size: Size in bytes
        checksum: SHA-256 checksum
        user_id: ID of the user who initiated the crawl
        **kwargs: Additional signal data
    """
    try:
        await sync_to_async(_save_archive_record)(
            job_id, url, blob_key, format, size, checksum, user_id
        )
        logger.debug(f"Saved archive record: {blob_key} for job {job_id}")
    except Exception as e:
        logger.error(f"Failed to save archive record {blob_key}: {e}", exc_info=True)


@sync_to_async
def _save_archive_record(
    job_id: str,
    url: str,
    blob_key: str,
    format: str,
    size: Optional[int],
    checksum: Optional[str],
    user_id: Optional[int],
) -> None:
    """Synchronous helper to save an ArchiveRecord.

    Args:
        job_id: ID of the crawl job
        url: URL that was archived
        blob_key: Key/path in blob storage
        format: Archive format
        size: Size in bytes
        checksum: SHA-256 checksum
        user_id: ID of the user who initiated the crawl
    """
    from mirror_control_panel.models import CrawlJob

    with transaction.atomic():
        try:
            job = CrawlJob.objects.get(id=job_id)
        except CrawlJob.DoesNotExist:
            logger.warning(f"CrawlJob {job_id} not found, skipping archive save")
            return

        ArchiveRecord.objects.create(
            crawl=job,
            url=url,
            blob_key=blob_key,
            format=format,
            size=size,
            checksum=checksum or "",
            created_by_id=user_id,
        )


async def on_crawl_completed(
    job_id: str,
    success: bool,
    error: Optional[str] = None,
    **kwargs: Any,
) -> None:
    """Handle crawl_completed signal from Mirror Core.

    Updates the CrawlJob status.

    Args:
        job_id: ID of the crawl job
        success: Whether the crawl succeeded
        error: Optional error message if failed
        **kwargs: Additional signal data
    """
    try:
        await sync_to_async(_update_crawl_status)(job_id, success, error)
        logger.info(f"Updated crawl {job_id} status: {'succeeded' if success else 'failed'}")
    except Exception as e:
        logger.error(f"Failed to update crawl {job_id}: {e}", exc_info=True)


@sync_to_async
def _update_crawl_status(job_id: str, success: bool, error: Optional[str]) -> None:
    """Synchronous helper to update CrawlJob status.

    Args:
        job_id: ID of the crawl job
        success: Whether the crawl succeeded
        error: Optional error message if failed
    """
    from mirror_control_panel.models import CrawlJob

    try:
        job = CrawlJob.objects.get(id=job_id)
    except CrawlJob.DoesNotExist:
        logger.warning(f"CrawlJob {job_id} not found, skipping status update")
        return

    job.mark_completed(success=success, error=error)


async def on_crawl_started(
    job_id: str,
    execution_id: str,
    **kwargs: Any,
) -> None:
    """Handle crawl_started signal from Mirror Core.

    Updates the CrawlJob with execution ID.

    Args:
        job_id: ID of the crawl job
        execution_id: Mirror execution ID
        **kwargs: Additional signal data
    """
    try:
        await sync_to_async(_update_execution_id)(job_id, execution_id)
        logger.debug(f"Updated crawl {job_id} with execution ID {execution_id}")
    except Exception as e:
        logger.error(f"Failed to update execution ID for {job_id}: {e}", exc_info=True)


@sync_to_async
def _update_execution_id(job_id: str, execution_id: str) -> None:
    """Synchronous helper to update CrawlJob execution ID.

    Args:
        job_id: ID of the crawl job
        execution_id: Mirror execution ID
    """
    from mirror_control_panel.models import CrawlJob

    try:
        job = CrawlJob.objects.get(id=job_id)
    except CrawlJob.DoesNotExist:
        logger.warning(f"CrawlJob {job_id} not found, skipping execution ID update")
        return

    job.execution_id = execution_id
    job.save(update_fields=["execution_id"])


async def on_worker_heartbeat(
    worker_name: str,
    status: str = "online",
    **kwargs: Any,
) -> None:
    """Handle worker_heartbeat signal from Mirror Core.

    Updates or creates a Worker record.

    Args:
        worker_name: Name of the worker
        status: Worker status (online, busy, etc.)
        **kwargs: Additional signal data
    """
    try:
        await sync_to_async(_update_worker)(worker_name, status)
        logger.debug(f"Updated worker heartbeat: {worker_name}")
    except Exception as e:
        logger.error(f"Failed to update worker {worker_name}: {e}", exc_info=True)


@sync_to_async
def _update_worker(worker_name: str, status: str) -> None:
    """Synchronous helper to update Worker.

    Args:
        worker_name: Name of the worker
        status: Worker status
    """

    try:
        worker = Worker.objects.get(name=worker_name)
        worker.heartbeat()
        if worker.status != status:
            worker.set_status(status)
    except Worker.DoesNotExist:
        Worker.objects.create(
            name=worker_name,
            status=status,
        )


# ============================================================================
# Bridge Functions for Mirror Application
# ============================================================================


def connect_signals_to_app(app: Application) -> None:
    """Connect Django signal handlers to a Mirror Application instance.

    This allows the application's signal bus to trigger Django database
    operations.

    Args:
        app: Mirror Application instance
    """
    # Get the signal bus from the application
    bus = app.signal_bus

    # Subscribe handlers
    bus.subscribe("url_discovered", on_url_discovered)
    bus.subscribe("archive_created", on_archive_created)
    bus.subscribe("crawl_completed", on_crawl_completed)
    bus.subscribe("crawl_started", on_crawl_started)
    bus.subscribe("worker_heartbeat", on_worker_heartbeat)

    logger.info("Connected Django signal handlers to Application signal bus")
