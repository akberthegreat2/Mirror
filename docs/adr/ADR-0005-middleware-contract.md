# Middleware contract

**Status:** Accepted  
**Date:** 2026-08-05

## Context

Mirror needs middleware for retries, timeouts, logging, tracing, and other
cross-cutting concerns. Middleware must behave the same way the plugin loader
behaves for providers.

## Decision

Middleware MUST be built from a settings model or a settings object that the
application resolves. Middleware MAY short-circuit, retry, observe, or mutate
the request/result pair. Middleware MUST NOT mutate the registry or discover new
packages.

## Consequences

The framework gets one plugin contract for both providers and middleware.
