# Mirror

Mirror is an application framework for building web infrastructure.

See [ARCHITECTURE.md](ARCHITECTURE.md) for the full specification.

## Development

```bash
# Install dev tools
pip install -e .[dev]

# Install packages individually
pip install -e packages/mirror-core
pip install -e packages/mirror-fetch
pip install -e packages/mirror-fetch-httpx

# Run all tests
pytest

# Lint and format
ruff check .
ruff format .

# Type check
mypy .
```
