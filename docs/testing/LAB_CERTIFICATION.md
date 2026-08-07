# Lab certification

Mirror should be validated in layers.

## Level 0 — Install smoke test

Prove a package can be installed in a clean environment.

Examples:
- `pip install .`
- `pip install mirror-core`
- `pip install mirror-fetch`
- `pip install mirror-fetch-httpx`

## Level 1 — Import smoke test

Prove each package imports cleanly after installation.

Examples:
- `import mirror_core`
- `import mirror_fetch`
- `import mirror_fetch_httpx`

## Level 2 — Discovery smoke test

Prove the extension system sees the package.

Examples:
- capability manifest discovered
- provider manifest discovered
- settings validated
- descriptor registered

## Level 3 — Contract smoke test

Prove the package implements the published contract.

Examples:
- protocol compliance
- request/result validation
- settings validation
- error taxonomy exists

## Level 4 — Lab integration test

Prove the package works with the kernel and a reference provider.

Examples:
- fetch + httpx
- archive + warc
- normalize + text
- chunk + text
- embed + hash
- vector store + memory
- retrieval + memory

## Level 5 — End-to-end pipeline test

Prove multiple packages compose correctly.

Examples:
- fetch -> archive
- fetch -> scrape -> analyze
- normalize -> chunk -> embed -> vector store -> retrieval
- crawl -> fetch -> archive

## Level 6 — Failure-path test

Prove runtime behavior is correct when things fail.

Examples:
- timeout
- retry
- cancellation
- short-circuit middleware
- partial success
- dead-letter routing
- checkpoint and resume when implemented

## Level 7 — Offline kernel test

Prove the kernel works without network access.

These tests should cover:
- planner
- executor
- resource envelopes
- middleware
- signals
- extension lifecycle
- metadata
- storage
- workers
- scheduler

## Level 8 — Compatibility matrix

Prove package combinations stay valid.

Examples:
- core only
- core + fetch
- core + fetch + httpx
- core + fetch + playwright
- core + archive + warc
- core + normalize + chunk + embed + vectorstore
- core + knowledge slice + retrieval

## Level 9 — Benchmark and regression check

Track:
- planner latency
- executor overhead
- worker throughput
- provider latency
- memory growth
- retry cost
- middleware overhead
- import time
- startup time

## Online reference-site tests

Some capabilities need public test sites or official APIs.

These tests should live in a scheduled or opt-in suite so pull requests do not become flaky.

Reference site catalog lives in `LEGAL_TEST_SITES.md`.
