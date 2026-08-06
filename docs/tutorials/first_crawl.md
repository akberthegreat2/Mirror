# First crawl

This tutorial shows how to connect the crawl capability to Mirror Core without a
bundle layer.

Use the dedicated packages:

- `mirror_core`
- `mirror_fetch_httpx`
- `mirror_crawl`
- `mirror_archive`

The crawl package owns the crawl contract and the crawl-specific pipeline. The
fetch package owns HTTP fetching. The archive package owns archive output.

The important idea is the boundary, not the bundle.
