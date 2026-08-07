# Legal reference sites for tests

This catalog lists public sites and official APIs that are useful for feature and integration testing.

The rule is simple:

- prefer explicit test sites and official APIs;
- do not test against sites that forbid automation;
- keep live-network tests in a scheduled suite when they can be flaky.

## Tier 1 — General web scraping and crawling

- Books to Scrape — static HTML, pagination, extraction
- Quotes to Scrape — login/CSRF and scripted interactions
- Scrape This Site — pagination, AJAX, frames, session cookies
- WebScraper.io test sites — crawling layouts, pagination, load-more, infinite scroll
- The Internet — nested frames, shadow DOM, tricky DOM behaviors
- ScrapingCourse — pagination, JS rendering, login flows

## Tier 2 — Production-style practice

- web-scraping.dev — rate limits, GraphQL, login, block pages, cookie popups, hidden JSON, bad encoding
- HTTPBin — methods, headers, cookies, delays, redirects
- JSONPlaceholder — REST/API extraction

## Tier 3 — Browser automation

- QA Playground
- Automation Exercise
- UI Testing Playground
- LetCode
- SauceDemo
- DemoQA
- ACME Test
- GlobalsQA Banking
- AutomateNow Sandbox
- OrangeHRM Demo

## Tier 4 — OCR and document processing

- OCR-Quality dataset
- OpenDoc-Null-6K
- Openpdf-Analysis-Recognition
- olmOCR-bench
- locally generated sample PDFs with known content

## Tier 5 — RPA and forms

- RPA Challenge
- The Automation Challenge
- SauceDemo
- DemoQA
- ACME Test

## Tier 6 — Maps and geospatial

- Google Places API
- Google Maps Test API
- OpenStreetMap Nominatim
- MapBox Geocoding

## Tier 7 — Real estate

- RentCast API
- Happy Endpoint
- Realie API
- Homedata (UK)
- Zillow sample dataset

## Tier 8 — Social data and synthetic data

- Fake Profile Generator
- postpit
- Synthetic Social Media Data Generator
- TikTok VCE
- Instagram fake account dataset

## Tier 9 — Email verification

- Apify Email Verifier
- bloombox
- smtp-probe
- free email domain datasets

## Tier 10 — Proxy and network

- HTTPBin IP
- IPInfo
- WhatIsMyIP
- BrowserLeaks

## Tier 11 — LLM and AI extraction

- web-scraping.dev
- JSONPlaceholder
- Books to Scrape
- Wikipedia

## Tier 12 — Government and public records

- Data.gov
- EU Open Data Portal
- UK Data Service
- World Bank API
- SEC EDGAR

## Usage notes

- Keep legal reference sites in a non-blocking suite when they can rate-limit or change without warning.
- Use fixtures or cached artifacts for repeatable CI.
- Prefer API-based tests when the site offers a supported API.
