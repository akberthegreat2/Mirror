# Alpha Checklist

Mirror reaches alpha when all of the following are true.

Read this together with `docs/ALPHA_CONTRACT.md`, `docs/ARCHITECTURE.md`, and
`docs/RELEASE_CHECKLIST.md`.

- [x] `mirror_core` imports no capability-specific package.
- [x] Discovery works through entry points.
- [x] Middleware exists as a core contract.
- [x] Worker contracts exist in the core.
- [x] Signals exist as a core contract.
- [x] Fresh installs can run the smoke test.
- [x] `mirror startproject` works.
- [x] `mirror startapp` works.
- [x] `mirror doctor` works.
- [x] One capability can swap between two providers without changing the pipeline.
- [x] Docs explain the architecture and developer workflow.
- [x] CI gates are documented and reproducible.
- [x] A future contributor has a documented release checklist.
