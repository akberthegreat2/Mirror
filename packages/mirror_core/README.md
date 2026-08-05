# mirror-core

`mirror-core` is the capability-agnostic kernel of Mirror.

It provides discovery, registries, pipeline compilation, execution runs,
middleware composition, signals, typed resource envelopes, deterministic
settings, and transactional lifecycle management.

It intentionally contains no Fetch, Archive, HTTP, HTML, WARC, CLI, or other
domain-specific implementation.

## What it is for

Use `mirror-core` when you want:

- one place for framework behavior;
- stable contracts for plugins;
- a reusable execution engine;
- a framework that can grow without becoming monolithic.

## Runtime shape

```python
plan = Planner(registry, default_providers={"fetch": "httpx"}).plan(pipeline)
result = await executor.execute_run(
    plan,
    inputs={"url": "https://example.com"},
)
```

`Pipeline.inputs` declares accepted input names. Actual values are supplied at
execution time.

See `ARCHITECTURE.md` and `docs/implementation/core-hardening-phase-1.md` for
ownership and lifecycle guarantees.
