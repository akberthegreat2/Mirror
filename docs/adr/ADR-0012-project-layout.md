# ADR 0012 — Project layout

## Status
Accepted

## Context
New contributors should not have to invent a repository layout.

## Decision
`mirror startproject` SHALL generate a Django-style project shell.
`mirror startapp` SHALL add reusable app packages under `apps/`.

## Consequences
Projects and apps share one predictable layout.
