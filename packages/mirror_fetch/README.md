# Mirror Fetch

Mirror Fetch is the capability contract for retrieving web resources.

It gives Mirror a stable fetch interface while letting the backend change
between HTTP clients, browser automation, or future providers.

## Common uses

- fetch a page;
- download a file;
- retrieve metadata;
- keep the pipeline stable while switching backends.
