"""Management command to archive old audit logs to cold storage."""

import gzip
import json
from datetime import datetime, timedelta
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction

from mirror_control_panel.models import AuditLog


class Command(BaseCommand):
    """Archive old audit logs to cold storage."""

    help = "Archive audit logs older than retention period to cold storage"

    def add_arguments(self, parser) -> None:
        """Add command arguments."""
        parser.add_argument(
            "--retention-days",
            type=int,
            default=180,
            help="Days to keep in hot storage (default: 180)",
        )
        parser.add_argument(
            "--archive-path",
            type=str,
            default="/data/mirror/audit-archive",
            help="Path for cold storage archives (default: /data/mirror/audit-archive)",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=10000,
            help="Number of records to process per batch (default: 10000)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be archived without actually archiving",
        )

    def handle(self, *args, **options) -> None:
        """Handle the command."""
        retention_days = options["retention_days"]
        archive_path = Path(options["archive_path"])
        batch_size = options["batch_size"]
        dry_run = options["dry_run"]

        cutoff = datetime.now() - timedelta(days=retention_days)

        self.stdout.write(f"Archiving audit logs older than {cutoff.isoformat()}")

        # Count logs to archive
        count = AuditLog.objects.filter(timestamp__lt=cutoff).count()
        self.stdout.write(f"Found {count} logs to archive")

        if count == 0:
            self.stdout.write(self.style.SUCCESS("No logs to archive"))
            return

        if dry_run:
            self.stdout.write("DRY RUN: No logs will be archived")
            return

        # Create archive directory
        archive_path.mkdir(parents=True, exist_ok=True)

        # Generate filename
        filename = f"audit-{cutoff.strftime('%Y%m%d')}.jsonl.gz"
        filepath = archive_path / filename

        self.stdout.write(f"Archiving to {filepath}")

        archived_count = 0
        with gzip.open(filepath, "wt", encoding="utf-8") as f:
            # Process in batches
            while True:
                # Get batch of logs
                logs = list(
                    AuditLog.objects.filter(timestamp__lt=cutoff).order_by("timestamp")[:batch_size]
                )

                if not logs:
                    break

                # Write logs to archive
                with transaction.atomic():
                    for log in logs:
                        # Convert to dict
                        record = {
                            "user": log.user.username if log.user else None,
                            "action": log.action,
                            "resource_type": log.resource_type,
                            "resource_id": log.resource_id,
                            "changes": log.changes,
                            "timestamp": log.timestamp.isoformat(),
                            "ip_address": log.ip_address,
                            "user_agent": log.user_agent,
                            "metadata": log.metadata,
                        }
                        f.write(json.dumps(record) + "\n")

                    # Delete from hot storage
                    log_ids = [log.id for log in logs]
                    AuditLog.objects.filter(id__in=log_ids).delete()
                    archived_count += len(logs)

                self.stdout.write(f"Archived {archived_count} logs...")

        self.stdout.write(self.style.SUCCESS(f"Archived {archived_count} logs to {filepath}"))
