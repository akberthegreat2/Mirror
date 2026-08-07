# PR: Phase five ecosystem expansion

## Problem

Mirror needs a home for the next wave of optional capability families without turning the kernel into a domain-specific framework.

## Decision

Document the broader capability catalog as optional ecosystem growth built on the same contract/provider model.

## What changed

- added a capability-expansion ADR for vertical and cross-domain packages;
- documented future families such as OCR, PDF, tables, stealth, proxies, RPA, LLM parsing, agentic crawl, maps, social collection, real estate, government portals, email verification, observability, webhooks, and privacy/compliance;
- kept the core AI-agnostic and vendor-neutral;
- made it clear that these are optional packages, not kernel requirements.

## Validation

- the catalog is documented as a future ecosystem direction, not as a hard beta commitment;
- the same package rules apply to every future family.

## Deferred

- concrete provider packages for each family;
- production hardening for each vertical integration;
- individual package READMEs and reference docs for every future capability.
