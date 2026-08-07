# mirror-core

`mirror-core` is the capability-agnostic kernel of Mirror. It provides extension manifests, immutable registries, a trusted pipeline compiler, isolated execution runs, middleware composition, signals, typed resource envelopes, deterministic settings, transactional application lifecycle, and a dedicated metadata contract in `mirror_core.metadata`.

Blob storage remains in `mirror_core.storage`, while metadata storage is exposed through `mirror_core.metadata` and re-exported from `mirror_core.storage` for compatibility.

It intentionally contains no Fetch, Archive, HTTP, HTML, WARC, CLI, or other domain implementation.

## Runtime contract

```python
plan = PipelineCompiler(registry, default_providers={"fetch": "httpx"}).compile(pipeline)
result = await executor.execute_run(
    plan,
    inputs={"url": "https://example.com"},
)
```

`Pipeline.inputs` declares accepted input names. Actual values are supplied at execution time.

See the repository `ARCHITECTURE.md` and `docs/implementation/core-hardening-phase-1.md` for ownership and lifecycle guarantees.
