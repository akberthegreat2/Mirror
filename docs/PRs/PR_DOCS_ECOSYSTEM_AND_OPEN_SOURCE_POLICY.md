# PR: documentation ecosystem expansion and open-source-first policy

## Summary

This note records the documentation pass that:
- rewrote the top-level README into a more user-facing introduction;
- generalized the architecture contract so it reads like a constitutional document;
- added a dedicated ecosystem catalog for current and future capability families;
- added lab-certification and legal test-site documentation;
- added a proposed ADR for the open-source-first provider policy.

## Why this changed

Mirror has grown beyond its original web-crawler framing.
The documentation now needs to speak for the current kernel and the future ecosystem without depending on chat history.

The README should answer:
- what Mirror does;
- how Mirror works;
- how to try it;
- how to use it in a custom project;
- what is planned next.

The architecture document should remain boring, general, and protective of the kernel.

The ecosystem catalog should hold the long-tail capability families so they do not pollute the architecture contract.

## What is deferred

- the extension-system migration audit remains a beta gate;
- proprietary vendor plugins remain optional and external;
- far-future capability families remain cataloged, not promised as beta deliverables.
