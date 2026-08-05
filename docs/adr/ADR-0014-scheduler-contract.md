# ADR-0014: scheduler contract

Status: Accepted

## Decision

Mirror defines a scheduler contract that can list due jobs, pause and resume
entries, and mark a job as run.

## Reason

The framework needs recurring crawls and monitors without hard-coding a single
queue engine.
