# Capabilities and providers

Mirror separates **what** a workflow needs from **how** that capability is
implemented.

A capability publishes a contract:

```text
Fetch
Crawl
Archive
Search
Analyze
Scrape
Diff
Monitor
...
```

A provider implements one of those contracts:

```text
Fetch → HTTPX
Fetch → Playwright
Archive → WARC
...
```

The planner resolves the pair before execution. The executor then consumes the
compiled pair; it does not guess a provider at runtime.

## Why this matters

A worker must not contain code such as:

```python
if capability == "crawl":
    use_scrapy()
elif capability == "fetch":
    use_httpx()
```

That would couple infrastructure to business capabilities.

Instead:

```text
Scheduler
   ↓
WorkerBackend
   ↓
Execution mechanism
   ↓
Core Executor
   ↓
compiled capability/provider pair
```

Providers remain independently installable and replaceable.
