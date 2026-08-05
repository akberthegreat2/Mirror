# Storage

Mirror separates two kinds of saved data:

- **metadata** — small structured records such as runs, schedules, URLs, and checkpoints
- **blobs** — larger content such as HTML, screenshots, archives, or exported files

Why split them?

- metadata needs fast lookup and filtering
- blobs are larger and belong in object storage or the filesystem
- the same crawler should work whether the payload is local or remote

Typical setup:

- SQLite or PostgreSQL for metadata
- filesystem, S3, or MinIO for blobs

That gives Mirror a simple development story and a production story.
