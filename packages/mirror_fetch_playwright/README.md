# mirror-fetch-playwright

Playwright-style provider package for the Mirror Fetch capability.

This package proves that Mirror can swap fetch providers without changing the
pipeline definition. The provider is intentionally lightweight so the package
remains installable in constrained environments and can still be tested without
network access.
