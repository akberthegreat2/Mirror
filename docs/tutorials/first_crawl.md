# First crawl

This tutorial shows the smallest useful crawl.

## What you need

- a Mirror project
- a fetch provider
- a place to store discovered URLs

## Example

```python
from mirror_core.storage import InMemoryBlobStore, InMemoryMetadataStore
from mirror_crawl.models import CrawlRequest
from mirror_crawl.provider import LocalCrawlProvider

provider = LocalCrawlProvider()
metadata_store = InMemoryMetadataStore()
blob_store = InMemoryBlobStore()

result = await provider.crawl(
    CrawlRequest(url="https://example.com", max_depth=1),
)
```

Mirror will:

- fetch the first page
- follow same-host links
- save the URLs it found
- store page content when requested

That is enough to build a crawler-backed SaaS workflow.
