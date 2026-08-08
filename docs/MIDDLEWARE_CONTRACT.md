# Middleware Contract

Middleware is a core contract. It wraps execution and may observe, transform, short-circuit, or annotate work.

## Scopes

- application or global middleware
- capability middleware

## Construction contract

Middleware is instantiated from a validated settings model, the same way providers are.
The application bootstrap resolves the manifest, validates settings, and creates
one middleware instance per named middleware. Middleware invocations now carry
ExecutionContext and CapabilityContext objects so cross-cutting concerns can
observe the same runtime snapshot as the executor.

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
Middleware order is part of the runtime contract: declarations execute in sequence, and the final handler sees the same invocation snapshot that upstream middleware observed.

## Short-circuiting

A middleware may return a result without calling the next middleware.
That is a supported control-flow decision, not an error.

## Policy ownership

Retry, timeout, and cancellation are execution policies.
Middleware may enforce them, but the policy definition belongs to the core runtime contract. Fallback is supported as a step-level execution policy; fallback providers are resolved by Core before the middleware chain is invoked.

## Construction rule

Middleware and providers are constructed through manifest-backed settings
objects. The repository uses one contract for plugin construction so tests can
exercise the same path that Application uses.
