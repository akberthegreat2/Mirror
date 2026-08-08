# Mirror capability guide

A capability is a stable domain contract. A provider is the concrete backend that
implements it. Install only the capability and provider packages your
application needs.

| Capability | Contract package | Provider examples |
|---|---|---|
| Fetch | `mirror-fetch` | HTTPX, Playwright |
| Crawl | `mirror-crawl` | Scrapy, local/reference |
| Archive | `mirror-archive` | WARC |
| Search | `mirror-search` | Memory |
| Analyze | `mirror-analyze` | Basic |
| Scrape | `mirror-scrape` | Basic |
| Diff | `mirror-diff` | Text |
| Monitor | `mirror-monitor` | Memory |
| Normalize | `mirror-normalize` | Text |
| Enrich | `mirror-enrich` | Text |
| Chunk | `mirror-chunk` | Text |
| Dedup | `mirror-dedup` | Hash |
| Embedding | `mirror-embedding` | Hash |
| Retrieval | `mirror-retrieval` | Memory |
| Vector store | `mirror-vectorstore` | Memory |
| Provenance | `mirror-provenance` | Resource |
| Compliance | `mirror-compliance` | Rules |

The provider column describes packages actually present in this repository.
It is not a recommendation that an in-memory provider is suitable for a
production deployment.
