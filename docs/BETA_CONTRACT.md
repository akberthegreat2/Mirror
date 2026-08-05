# Beta contract

Mirror beta is the point where the framework must run real workloads, not just
prove its architecture.

## Beta requires

- a crawl capability that saves discovered URLs when asked
- worker backends that can run jobs locally and from SQLite state
- a scheduler that can produce due jobs again and again
- metadata storage for runs, URLs, schedules, and checkpoints
- blob storage for HTML and other large payloads
- retry and timeout policies that affect execution
- documentation that explains the product in plain language

## Beta stack

Mirror officially supports:

- SQLite for development metadata
- PostgreSQL for production metadata
- filesystem storage for development blobs
- S3-compatible storage for production blobs
- local workers for tests and examples
- SQLite-backed workers for single-machine beta setups

Redis and Celery remain the default distributed path for later production work,
but beta focuses first on the single-machine stack that contributors can run
anywhere.
