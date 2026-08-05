# ADR-0013: storage and blob boundaries

Status: Accepted

Mirror stores two different kinds of data.

## Decision

- metadata goes into a metadata store
- large content goes into a blob store
- the metadata store MUST support typed records
- the blob store MUST support binary payloads

## Reason

Crawling, archiving, and monitoring all produce metadata and large content.
Keeping them separate keeps the framework simple to run locally and simple to
scale later.
