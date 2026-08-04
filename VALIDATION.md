# Alpha Candidate Validation

Validation performed on 2026-08-04 against the final clean source snapshot.

## Passed

```text
pytest: 98 passed, 0 skipped
python -m compileall: passed
wheel builds: 9/9 passed
installed-wheel imports: passed
installed entry-point discovery: passed
CLI help from installed wheels: passed
```

Built distributions:

- mirror-core
- mirror-fetch
- mirror-fetch-httpx
- mirror-fetch-playwright
- mirror-archive
- mirror-archive-warc
- mirror-middleware
- mirror-cli
- mirror-testing

The installed-wheel smoke test used a clean target directory outside the
repository, ensuring imports and metadata came from the built wheels rather than
workspace source paths.

## WARC evidence

WARC tests no longer skip when `warcio` is unavailable. Deterministic writer
doubles verify:

- explicit and idempotent lifecycle;
- valid `create_warc_record` arguments for WARC resource records;
- payload digest and sanitized metadata headers;
- segment rotation;
- serialization of concurrent writes;
- error translation and exception chaining;
- the reusable Archive provider contract.

The production provider still requires the real `warcio` package. This runtime
environment did not contain `warcio`, so a real-file parse/readback test was not
performed here. That check remains required in CI before publishing the WARC
wheel.

## Unavailable quality gates

`ruff` and `mypy` were not installed in the execution environment. Run these in
Codespaces/CI before tagging:

```bash
ruff check .
ruff format --check .
make type
```
