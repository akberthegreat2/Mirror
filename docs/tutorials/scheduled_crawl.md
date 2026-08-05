# Scheduled crawl

Mirror can run the same crawl again and again.

## Example schedule

```python
from datetime import datetime, timezone

from mirror_core.scheduler import InMemoryScheduler, ScheduleRecord

scheduler = InMemoryScheduler()
scheduler.schedule(
    ScheduleRecord(
        name="crawl-example",
        due_at=datetime.now(timezone.utc),
        interval_seconds=21600.0,
        payload={"url": "https://example.com"},
    )
)
```

A scheduler gives you the missing loop for recurring jobs. It makes crawlers,
monitors, and archives useful in production.
