# Crawling

Mirror can walk through a website from a starting URL and remember what it finds.

A crawl can:

- visit the first page
- follow links on the page
- save the discovered URLs
- store page content in blob storage
- stop after a depth or page limit

Why this matters:

- a crawler that forgets what it saw is hard to build a SaaS on
- saved URLs let you re-run checks later
- stored pages let you compare changes over time

Example:

> Start at `https://example.com`, follow links on the same host, save every URL,
> and keep the HTML for later.

That is the kind of job Mirror is meant to handle.
