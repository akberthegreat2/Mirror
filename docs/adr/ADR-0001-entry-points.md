# ADR-0001: Use Entry Points for Extension Discovery

## Status
Accepted

## Context
Mirror needs a way to discover capabilities, providers, middleware, interfaces, and storage backends without hardcoding imports or requiring users to edit framework code. Traditional solutions include:
- Hardcoded lists in core.
- Configuration-based imports (import strings).
- Pluggy or similar plugin systems.
- Python’s `importlib.metadata` entry points.

## Decision
We will use Python entry points (via `importlib.metadata`) as the discovery mechanism for all extensions. Each extension type will have its own dedicated namespace:
- `mirror.capabilities`
- `mirror.providers`
- `mirror.middleware`
- `mirror.interfaces`
- `mirror.storage`

Extensions must export a descriptor object (e.g., `CapabilityConfig`, `ProviderConfig`) that is loaded and validated at application startup.

## Consequences
- Core imports nothing from extension packages.
- Discovery happens once at startup.
- Duplicate or invalid descriptors cause startup errors.
- Adding a new extension only requires installing a package; no core changes.
- The entry-point system is built into Python, so no external library needed.
- Tests can override discovery via an injectable source.

## Alternatives Considered
- **Hardcoded imports**: Violates “Core knows nothing” principle; requires core changes for every extension.
- **Configuration files**: Would require parsing and may not scale to installed packages.
- **Pluggy**: Adds external dependency; overkill for simple metadata discovery.

## Decision Rationale
Entry points are standard, well-supported, and allow zero-dependency discovery. They keep core clean and make extensions truly pluggable.
