# mirror-crawl reference

`mirror-crawl` adds the first crawl workflow on top of Mirror Fetch.

It provides:

- `CrawlRequest`
- `CrawlResult`
- `CrawlSettings`
- `LocalCrawlProvider`
- `crawl_site()`

The crawl provider can use HTTPX or Playwright fetch backends.
