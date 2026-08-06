# mirror-testing

Contract-testing utilities for Mirror providers and capabilities.

This package is installed as a regular distribution package, so the README
lives at the package root to satisfy build metadata and wheel generation.

## Usage

```python
from mirror_testing import BaseContract


class FetchContract(BaseContract):
    provider_class = HTTPXProvider
```
