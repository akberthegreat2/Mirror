# Capability packages

Mirror is split into separate capability packages. Each package owns one domain
contract and stays small on purpose.

## Package roles

| Package | Role |
| --- | --- |
| `mirror_core` | Framework kernel: planner, executor, registry, discovery, lifecycle, signals, middleware, storage, scheduler, workers |
| `mirror_fetch` | Fetch contract and request/result models |
| `mirror_fetch_httpx` | HTTPX provider for fetch |
| `mirror_fetch_playwright` | Playwright provider for fetch |
| `mirror_crawl` | Crawl contract and crawl-specific orchestration |
| `mirror_archive` | Archive contract and archive-specific orchestration |
| `mirror_archive_warc` | WARC archive provider |
| `mirror_scrape` | Scrape contract and extraction models |
| `mirror_analyze` | Analyze contract and analysis models |
| `mirror_diff` | Diff contract and comparison models |
| `mirror_search` | Search contract and search models |
| `mirror_monitor` | Monitor contract and monitoring models |
| `mirror_control_django` | Optional control-plane contract package |

## How to think about them

A capability package should answer one question only:

> What does this domain mean?

A provider package should answer one question only:

> How do I implement that domain?

`mirror_core` answers the framework question:

> How do all of these pieces run together safely?

That is the separation Mirror follows now.
