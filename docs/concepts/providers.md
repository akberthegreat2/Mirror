# Providers

Providers implement capability contracts.

Mirror keeps the capability contract stable and lets the implementation vary.
That is how one pipeline can run against multiple backends without changing the
pipeline itself.

## Example

The Fetch capability can use different providers:

- `mirror-fetch-httpx`
- `mirror-fetch-playwright`

Both packages expose a `ProviderManifest` manifest through entry points. Mirror
Core resolves the selected provider at runtime from settings.
