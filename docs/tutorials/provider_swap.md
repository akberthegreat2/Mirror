# Tutorial: swap a Fetch provider

This tutorial shows one of Mirror's main ideas: the pipeline stays the same
while the backend changes.

## 1. Install the packages

```bash
pip install mirror-core mirror-fetch mirror-fetch-httpx mirror-fetch-playwright
```

## 2. Write one pipeline

```python
from mirror_core.pipeline import Pipeline, Step

pipeline = Pipeline(
    id="fetch-homepage",
    inputs={"url": "str"},
    steps=[
        Step(
            id="fetch",
            capability="fetch",
            input={"url": "$pipeline.url"},
            outputs=["result"],
        )
    ],
)
```

## 3. Choose a provider

```python
components = {"fetch": {"provider": "httpx"}}
```

Change only `httpx` to `playwright` when you want a browser backend.

The pipeline does not need to change.
