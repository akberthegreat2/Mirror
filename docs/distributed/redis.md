# Redis broker

Mirror uses Redis through Celery's supported Redis transport.

Redis carries messages such as:

```text
mirror.default
mirror.io
mirror.cpu
mirror.gpu
```

These names represent **execution classes**. They do not represent capabilities.

Redis is deliberately not the durable job store. PostgreSQL records the job and
its lease before Celery publishes the execution ID.

## Local service

The supplied Docker Compose file uses:

```text
redis:8-alpine
```

The broker URL is:

```text
redis://redis:6379/0
```
