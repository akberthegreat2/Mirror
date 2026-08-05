# Scheduler reference

The scheduler contract lets Mirror store recurring jobs, pause them, resume
them, and ask which jobs are due.

Implemented backends:

- `InMemoryScheduler`
- `SQLiteScheduler`
