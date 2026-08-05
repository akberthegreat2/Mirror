# Middleware Contract

Middleware is a core contract. It wraps execution and may observe, transform, short-circuit, or annotate work.

## Scopes

- application middleware
- pipeline middleware
- capability middleware
- step middleware

## What middleware may do

- inspect the invocation
- add tracing or metrics context
- modify input or output
- short-circuit with a cached, mocked, or substituted result
- raise
- retry
- delegate to the next middleware

## What middleware should not do

- discover components
- mutate the application registry
- recompile the pipeline
- invent provider resolution rules

## Ordering

Ordering must be explicit and deterministic.
The compiled chain should honor declared ordering constraints and applicability rules.

## Short-circuiting

A middleware may return a result without calling the next middleware.
That is a supported control-flow decision, not an error.

## Policy ownership

Retry, timeout, fallback, and cancellation are execution policies.
Middleware may enforce them, but the policy definition belongs to the core runtime contract.
