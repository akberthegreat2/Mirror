# Mirror Handover

Repository state: ADR-0025, ADR-0026, ADR-0027, ADR-0028, ADR-0029, ADR-0030, ADR-0031, and ADR-0032 are implemented and tightened in the current snapshot.

What changed:
- Kept the runtime kernel centered in `mirror_core`.
- Added ADR-0029 runtime contracts for fallback/checkpoint/compensation policies.
- Persisted per-step checkpoints through the core executor when a checkpoint store is present.
- Added dead-letter queue contracts plus in-memory and SQLite implementations for terminal failures.
- Recorded terminal failures through the executor into the dead-letter queue when one is configured.
- Added a dedicated `mirror_core.metadata` module for operational metadata records and durable metadata stores.
- Kept `mirror_core.storage` focused on blob storage while re-exporting metadata contracts for compatibility.
- Added core scheduling semantics, `SchedulerCoordinator`, and a durable scheduler backend contract.
- Added core worker runtime helpers plus local and SQLite worker backends, execution stores, and lease managers.
- Preserved the future ADR drafts under `docs/adr/future/` for ADR-0031 and ADR-0032.

Current verification:
- `pytest -q` → 256 passed

Scope intentionally left unchanged:
- The core remains framework-only; capabilities still own domain logic only.
- Future worker and scheduler ADR drafts remain preserved for reference.
