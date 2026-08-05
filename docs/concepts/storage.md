# Storage

Mirror separates metadata from blobs.

- Metadata is the small, queryable information stored in a database.
- Blobs are the large payloads stored in a blob store or filesystem backend.

Why this matters:

- database rows stay light;
- large HTML, WARC, screenshots, and JSON dumps stay out of the database;
- data can move between local development and production storage without changing the pipeline.
