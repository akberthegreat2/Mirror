# Storage reference

Mirror separates metadata storage from blob storage. Metadata contracts live in `mirror_core.metadata`; blob storage lives in `mirror_core.storage`.

## Metadata storage

Metadata storage holds small records such as runs, steps, schedules, and URL
records.

## Blob storage

Blob storage holds large payloads such as HTML, WARC, screenshots, or exports.

## Why this split exists

The split keeps the database fast and makes large payloads easy to move between
local development and production backends.
