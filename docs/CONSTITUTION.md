# Mirror documentation constitution

This repository uses three documentation voices.

## 1. Product voice

Product docs are for people who want to understand what Mirror does.

They MUST answer:

- what Mirror is for;
- what a user can build;
- how to start quickly;
- what ships today;
- what is intentionally deferred.

Product docs MUST be written in plain language.

## 2. Contributor voice

Contributor docs are for people who change the framework.

They MUST answer:

- what may change;
- what must not change;
- which packages own which responsibilities;
- which invariants are frozen;
- which changes require an ADR.

Contributor docs MUST be strict and unambiguous.

## 3. Reference voice

Reference docs are for programmers who need exact behavior.

They MUST describe:

- commands;
- functions;
- classes;
- parameters;
- return values;
- errors;
- examples.

Reference docs MUST be precise and complete.

## Documentation rules

- If code, tests, and docs disagree, the change is incomplete.
- Every architecture decision MUST appear in an ADR.
- Every public command SHOULD appear in the README or a user guide.
- Every callable public API MUST have a docstring and a reference entry.
- No document in `docs/` should depend on chat history to make sense.

## What belongs where

- `README.md` → product overview.
- `getting-started/` → first steps.
- `tutorials/` → step-by-step examples.
- `reference/` → API and command reference.
- `architecture/` and `docs/adr/` → maintainer contract and decisions.

If a document feels too technical for users, move the detail to reference or architecture docs.
