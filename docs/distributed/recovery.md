# Distributed recovery

Mirror treats worker execution as at-least-once infrastructure delivery with
Core-owned execution semantics.

## Worker crash

A worker claims one job and receives a PostgreSQL lease. If the process dies,
it stops renewing that lease. After expiry another worker may reclaim the job.

## Duplicate delivery

Celery may deliver a message more than once. The worker therefore claims the
specific durable job ID before executing it. A job that is already terminal or
owned by another live worker is not executed again by the second delivery.

## Redis restart

Redis contains transport messages, not the durable state of the execution.
After Redis recovery, queued jobs can be republished from PostgreSQL by a
reconciliation process.

## PostgreSQL restart

PostgreSQL is the durable authority. Workers fail closed when it is unavailable
rather than inventing a second state store.

## Retry

Retry policy belongs to Mirror Core. Celery's `acks_late` and worker-loss
settings provide delivery safety; they do not define whether a failed step is
retried.
