# Pre-alpha Status

Mirror's core architecture is stable enough for product prototyping and for building the first SaaS application on top of the local execution path.

## Implemented and tested

- Independent package distributions.
- Capability/provider discovery through typed entry-point descriptors.
- Transactional Application lifecycle and provider ownership through `ComponentManager`.
- Immutable pipeline planning with semantic capability/provider resolution.
- Dependency-ready DAG scheduling with bounded concurrency.
- Explicit runtime inputs, retry, timeout, cancellation, and supported error policies.
- Capability-scoped middleware chains and middleware short-circuiting.
- Typed resources with fingerprints, producer identity, and direct-parent lineage.
- HTTPX and real Playwright Fetch providers.
- Typed Archive capability and hardened WARC provider.
- CLI project scaffolding, descriptor inspection, and pipeline execution.
- Provider contract-test helpers.

## Experimental

- Worker, execution-store, checkpoint, artifact-store, and lease contracts.
- These APIs are intentionally not promoted from the `mirror_core` root and are not presented as distributed execution.

## Deferred

- Durable distributed scheduling and workers.
- Production lease/fencing semantics.
- Remote object-storage providers.
- Schema migration and durable polymorphic resource reconstruction.
- REST, Django Admin, dashboard, and other interface packages.
- Full dynamic DAG optimizations and fan-out/fan-in primitives.

## Release position

This repository is an alpha candidate, not a production-scale distributed platform. It is suitable for beginning SaaS development against the local execution API while operational capabilities are added as separate packages driven by product requirements.
