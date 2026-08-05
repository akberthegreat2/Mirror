# PR Core Phase 2 — Provider Swap

## Summary

Add a second Fetch provider package, `mirror-fetch-playwright`, and a real
integration test proving that the same pipeline runs with either provider.

## Why

Mirror's modularity promise depends on backend swapping working without pipeline
rewrites.

## What changed

- Added a new provider package and tests.
- Updated Fetch capability typing so pipeline inputs follow the request model.
- Added docs for provider selection and swapping.
- Added smoke coverage for the new package.

## Follow-ups

- Replace the lightweight backend with a true browser backend when the optional
  Playwright dependency is available.
- Add startapp/project scaffolding polish after modularity is proven.
