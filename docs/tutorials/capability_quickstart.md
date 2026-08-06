# Quick start: one capability at a time

This tutorial shows the Mirror way to start small.

## Goal

Build with one capability and `mirror_core` only.

## Example: search only

If you only need search, install the core plus the search capability package and
its provider package. Keep everything else out of the environment until you need
it.

Then work with the search contract directly:

```python
from mirror_search import SearchRequest, build_memory_search_provider, run_search

provider = build_memory_search_provider(settings={"seed_documents": []})
result = await run_search(provider, SearchRequest(query="mirror", limit=5))
print(result.hits)
```

The pattern is always the same:

1. install `mirror_core`;
2. install one capability package;
3. install one provider package;
4. run the capability through its contract.

When you need another capability, add only that package and its provider.
