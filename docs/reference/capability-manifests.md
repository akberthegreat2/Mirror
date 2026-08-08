# Capability manifests

Every shipped Mirror capability publishes a `CapabilityManifest` through the
canonical `mirror.capabilities` entry-point group. The manifest is the stable
metadata surface consumed by discovery, validation, CLI tooling, and future
Django/REST interfaces.

A capability manifest describes at minimum:

- capability name and API version;
- request and result models;
- runner/protocol information;
- input/output ports where declared;
- capability dependencies;
- human-readable metadata.

## Shipped capabilities

| Capability | Package | API | Current first-party provider(s) |
| --- | --- | --- | --- |
| Analyze | `mirror-analyze` | 1.0.0 | `mirror-analyze-basic` |
| Archive | `mirror-archive` | 1.0 | `mirror-archive-warc` (WARC) |
| Chunk | `mirror-chunk` | 1.0.0 | `mirror-chunk-text` |
| Compliance | `mirror-compliance` | 1.0.0 | `mirror-compliance-rules` |
| Crawl | `mirror-crawl` | 1.0 | `mirror-crawl-local`, `mirror-crawl-scrapy` |
| Dedup | `mirror-dedup` | 1.0.0 | `mirror-dedup-hash` |
| Diff | `mirror-diff` | 1.0.0 | `mirror-diff-text` |
| Embedding | `mirror-embedding` | 1.0.0 | `mirror-embedding-hash` |
| Enrich | `mirror-enrich` | 1.0.0 | `mirror-enrich-text` |
| Fetch | `mirror-fetch` | 1.0 | `mirror-fetch-httpx`, `mirror-fetch-playwright` |
| Monitor | `mirror-monitor` | 1.0.0 | `mirror-monitor-memory` |
| Normalize | `mirror-normalize` | 1.0.0 | `mirror-normalize-text` |
| Provenance | `mirror-provenance` | 1.0.0 | `mirror-provenance-resource` |
| Retrieval | `mirror-retrieval` | 1.0.0 | `mirror-retrieval-memory` |
| Scrape | `mirror-scrape` | 1.0.0 | `mirror-scrape-basic` |
| Search | `mirror-search` | 1.0.0 | `mirror-search-memory` |
| Vector store | `mirror-vectorstore` | 1.0.0 | `mirror-vectorstore-memory` |

Providers remain separate packages. Mirror does not replace established
backends with hidden implementations; for example, Scrapy is the Crawl
provider engine and HTTPX/Playwright are Fetch providers.

## Interface manifests

The same extension mechanism now publishes the shipped interfaces:

| Interface | Package | Purpose |
| --- | --- | --- |
| CLI | `mirror-cli` | terminal operations and project tooling |
| Dashboard | `mirror-control-django` | Django admin/control plane |
| REST | `mirror-control-api` | Django REST Framework control plane |

The interface catalog is intentionally framework-neutral. Django and DRF are
optional consumers of the Core catalog rather than dependencies of Core.

## Certification

`packages/mirror_core/tests/test_ecosystem_manifests.py` verifies that every
capability entry point resolves to a real `CapabilityManifest`, every provider
entry point resolves to a `ProviderManifest` when its optional dependencies are
available, and the three shipped interfaces publish `InterfaceManifest`
objects.
