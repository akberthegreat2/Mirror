# Middleware

Middleware is the layer that sits around a task and can observe or change what
happens.

## What middleware is good for

- retries
- timeouts
- rate limits
- logging
- tracing
- cache hits
- test doubles
- request enrichment

## What middleware may do

A middleware can:

- inspect the current step;
- change the request or the result;
- stop the call early;
- retry the call;
- add logging or trace data.

## What middleware should not do

Middleware should not choose the project structure or re-discover packages.
Those jobs belong to the application and the planner.
