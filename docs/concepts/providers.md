# Providers

A provider is the part that does the actual work behind a capability.

Mirror keeps the task the same and lets the backend change.

## Example

The Fetch capability can use different providers:

- `mirror-fetch-httpx` for plain HTTP requests
- `mirror-fetch-playwright` for browser-based fetching

That means you can keep the same pipeline and change the engine under it.
