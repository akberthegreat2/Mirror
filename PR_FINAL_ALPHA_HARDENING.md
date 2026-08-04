# PR: Final alpha hardening and WARC integrity

## Summary

This PR turns the existing modular framework snapshot into a truthful alpha
candidate. It does not add new capabilities. It hardens what already exists,
removes skipped contract coverage, fixes WARC record construction, and proves
that every distribution builds and is discoverable from installed wheels.

## WARC corrections

- Use `warcio`'s WARC resource-record API correctly.
- Stop passing WARC headers as HTTP headers.
- Let `warcio` create mandatory WARC fields.
- Add payload digest, resource reference, content type, and sanitized metadata.
- Keep lifecycle explicit and idempotent.
- Move blocking file/writer operations off the event loop.
- Serialize concurrent writes.
- Rotate segments before configured record/byte limits.
- Preserve underlying write/open failures as chained `ArchiveError` causes.
- Add deterministic tests independent of optional `warcio` availability.

## Contract-test corrections

- Remove placeholder skipped tests from the shared base contract.
- Make capability packages own concrete provider contracts.
- Enable the HTTPX structural contract explicitly.
- Replace external-network contract behavior with deterministic package tests.

## Validation

- 98 tests passed; zero skipped.
- All Python sources compile.
- Nine wheels build successfully.
- Imports and entry-point discovery work from installed wheels outside the repo.
- CLI help works from installed wheels.

## Remaining release gate

Run Ruff, Ruff format-check, mypy, and a real `warcio` round-trip test in CI
before tagging `v0.1.0-alpha`.
