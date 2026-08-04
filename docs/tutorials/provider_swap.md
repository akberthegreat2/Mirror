# Tutorial: Swapping a Fetch provider

This tutorial demonstrates the modularity contract.

## 1. Install the packages

```bash
pip install mirror-core mirror-fetch mirror-fetch-httpx mirror-fetch-playwright
```

## 2. Define one pipeline

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

## 3. Select a provider in settings

```python
components = {"fetch": {"provider": "httpx"}}
```

Switching the provider to `playwright` should not require a pipeline rewrite.
