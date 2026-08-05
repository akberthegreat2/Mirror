# Scheduler reference

A scheduler decides when jobs should run.

Mirror currently treats scheduling as a backend contract. The scheduler can:

- queue a job for later;
- pause a job;
- resume a job;
- hand work to workers.
