# Middleware

Middleware is a core Mirror contract. It wraps capability invocation and may
observe, modify, short-circuit, retry, or annotate execution.

## Contract

The core middleware API uses the `Invocation` model and the `Middleware`
protocol from `mirror_core.middleware`. Middleware descriptors also carry a
validated settings model so the application bootstrap can construct middleware
through the same descriptor-driven path as providers.

## What middleware may do

- inspect the resolved step and request;
- attach context for tracing or metrics;
- short-circuit with a cached or mock result;
- retry or raise;
- pass control to the next middleware in the chain.

## What middleware should not do

Middleware should not discover providers or mutate the application registry.
Those responsibilities belong to the application bootstrap and planner.
