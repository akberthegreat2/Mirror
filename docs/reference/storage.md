# Storage reference

Mirror storage is split into:

- `MetadataStore` for structured records
- `BlobStore` for binary content

The core package includes in-memory and SQLite-backed metadata stores plus an
in-memory and filesystem blob store.
