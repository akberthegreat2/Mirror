# mirror-testing

Contract‑testing utilities for Mirror providers.

## Usage

```python
from mirror_testing import ContractTestCase, CapabilityContract

class FetchContract(CapabilityContract):
    @staticmethod
    def create_provider(settings=None):
        return HTTPXProvider(settings)

    @staticmethod
    def valid_request():
        return FetchRequest(url="https://example.com")

    @staticmethod
    def invalid_request():
        return FetchRequest(url="not-a-url")

class TestFetchHTTPX(ContractTestCase):
    capability_contract = FetchContract
```
