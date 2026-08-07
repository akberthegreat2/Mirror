# mirror_fetch_playwright

The `mirror_fetch_playwright` package provides a second Fetch provider so Mirror
can prove backend swapping without changing pipeline definitions.

## Public exports

- `PlaywrightProvider`
- `PlaywrightSettings`
- `provider`

## Manifest

The package registers a `ProviderManifest` named `playwright` for capability
`fetch`.
