# Known Limitations

The alpha deliberately exposes only contracts that have working implementations.

1. **Execution is local and in-process.** Worker persistence contracts are provisional and are not a durable distributed runtime.
2. **Scheduling is dependency-ready within one process.** Admission control across machines, tenants, and queues is deferred.
3. **Large payload durability is not complete.** `BlobReference` provides the boundary, but production S3/GCS/Azure providers and schema reconstruction are not included.
4. **Playwright requires browser installation.** Install the provider package and run `playwright install chromium` before selecting it.
5. **WARC requires `warcio`.** WARC tests are dependency-gated when it is unavailable.
6. **YAML is optional.** Install PyYAML before loading YAML settings, pipeline, or input files.
7. **Static analysis remains a CI gate.** Ruff and mypy were unavailable in the packaging review environment and must pass before tagging.
8. **Public API is intentionally small.** Experimental worker and storage machinery must be imported from their submodules and may change during alpha.
