# Mirror Core

`mirror-core` is the framework kernel. It does not contain the implementations
of Fetch, Crawl, Search, Scrape, or other business capabilities.

Core owns:

- discovery and extension validation;
- settings precedence;
- pipeline compilation and provider resolution;
- execution plans and runtime contexts;
- executor semantics;
- retry, timeout, fallback, and cancellation policy;
- middleware and signals;
- scheduling;
- worker contracts and leases;
- storage and metadata contracts;
- lifecycle and transactional startup.

## Typical flow

```text
Pipeline definition
      ↓
PipelineCompiler
      ↓
ExecutionPlan
      ↓
Executor
      ↓
Capability provider
      ↓
ResourceEnvelope
```

The same plan can run through an inline worker during development or through the
Celery execution mechanism in a distributed deployment.
