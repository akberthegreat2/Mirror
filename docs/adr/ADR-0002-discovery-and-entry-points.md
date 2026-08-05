# ADR 0002 — Discovery and entry points

## Status
Accepted

## Context
The framework needs a standard way to find installed plugins without hardcoding
package names.

## Decision
Installed packages SHALL be discovered through Python entry points. Mirror MUST
not use hardcoded plugin lists.

## Consequences
Capabilities, providers, middleware, interfaces, and storage adapters become
installable without editing core registries.
