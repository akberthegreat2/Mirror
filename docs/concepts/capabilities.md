# Capabilities

Mirror is built from small, replaceable capability packages.

A capability package describes the job:

- fetch a page;
- crawl a site;
- archive a resource;
- scrape structured content;
- analyze text;
- compare versions;
- search indexed documents;
- monitor for change.

The package does **not** own the framework. The framework lives in
`mirror_core`.

## The simple rule

If a file decides *how the framework runs*, it belongs in `mirror_core`.
If a file decides *what a domain means*, it belongs in the capability package.
If a file decides *how to implement the capability*, it belongs in a provider
package.

That rule keeps Mirror from turning into a second framework.
