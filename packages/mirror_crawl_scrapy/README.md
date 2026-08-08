# Mirror Crawl — Scrapy provider

This package implements Mirror's Crawl capability using the established
[Scrapy](https://scrapy.org/) crawler framework. Mirror owns the capability
contract and orchestration; Scrapy owns crawling behavior.

Install:

```bash
pip install mirror-crawl mirror-crawl-scrapy
```

Select it explicitly as the `crawl` provider. Do not add crawler logic to Core
or to a Celery worker.
