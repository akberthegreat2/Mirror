# mirror-core

`mirror-core` is the capability-agnostic kernel of Mirror. It provides extension descriptors, immutable registries, pipeline compilation, isolated execution runs, middleware composition, signals, typed resource envelopes, deterministic settings, and transactional application lifecycle.

It intentionally contains no Fetch, Archive, HTTP, HTML, WARC, CLI, or other domain implementation.

## Runtime contract

```python
plan = Planner(registry, default_providers={"fetch": "httpx"}).plan(pipeline)
result = await executor.execute_run(
    plan,
    inputs={"url": "https://example.com"},
)
```

`Pipeline.inputs` declares accepted input names. Actual values are supplied at execution time.

See the repository `ARCHITECTURE.md` and `docs/implementation/core-hardening-phase-1.md` for ownership and lifecycle guarantees.
